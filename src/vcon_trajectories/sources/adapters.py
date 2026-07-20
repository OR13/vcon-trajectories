"""Per-source adapters: raw dataset record -> `UTrajectory` (see ir.py).

Each function is intentionally small; all the vCon logic lives in the shared
converter. Adapters are tolerant of missing/None fields since real records vary.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .ir import (ACTION, HANDOFF, MESSAGE, OBSERVATION, REASONING, TOOL_CALL,
                 TOOL_RESULT, Turn, UTrajectory)


def _maybe_json(s: Any) -> Any:
    if isinstance(s, str):
        try:
            return json.loads(s)
        except Exception:
            return s
    return s


def _parse_dt(s: Any) -> Optional[datetime]:
    if isinstance(s, datetime):
        return s
    if isinstance(s, str):
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def _excerpt(text: Optional[str], n: int = 80) -> str:
    return " ".join((text or "").split())[:n]


def _first_user_text(turns: List[Turn]) -> str:
    for t in turns:
        if t.kind == MESSAGE and t.role == "user" and t.text:
            return _excerpt(t.text)
    return ""


# --- shared shape parsers ----------------------------------------------------

def _openai_turns(messages: List[Dict[str, Any]]):
    """OpenAI chat-completions messages -> (system_prompt, turns).

    Handles assistant `tool_calls` (arguments as JSON string) and `role:"tool"`
    results. A `think` tool call is treated as a reasoning step.
    """
    system: Optional[str] = None
    turns: List[Turn] = []
    for m in messages or []:
        role = m.get("role")
        content = m.get("content")
        if role == "system":
            if content and system is None:
                system = content
        elif role == "user":
            if content:
                turns.append(Turn(MESSAGE, "user", role="user", text=content))
        elif role == "assistant":
            if isinstance(content, str) and content.strip():
                turns.append(Turn(MESSAGE, "assistant", role="assistant", text=content))
            for tc in (m.get("tool_calls") or []):
                fn = tc.get("function", {}) or {}
                name = fn.get("name")
                args = _maybe_json(fn.get("arguments"))
                if name == "think":
                    thought = args.get("thought") if isinstance(args, dict) else str(args)
                    turns.append(Turn(REASONING, "assistant", role="assistant", text=thought))
                else:
                    turns.append(Turn(TOOL_CALL, "assistant", role="assistant",
                                      tool_name=name, tool_input=args, meta={"id": tc.get("id")}))
        elif role == "tool":
            name = m.get("name") or "tool"
            turns.append(Turn(TOOL_RESULT, name, role="tool", tool_name=name,
                              tool_result=_maybe_json(content), meta={"id": m.get("tool_call_id")}))
    return system, turns


def _anthropic_turns(events: List[Dict[str, Any]]) -> List[Turn]:
    """Native Anthropic-style events (`{type, timestamp, message:{role,content}}`)
    where content is a string or a list of text/thinking/tool_use/tool_result blocks."""
    turns: List[Turn] = []
    tool_by_id: Dict[str, str] = {}
    for e in events or []:
        if e.get("type") not in ("user", "assistant"):
            continue
        ts = e.get("timestamp")
        msg = e.get("message") or {}
        role = msg.get("role") or e.get("type")
        content = msg.get("content")
        actor = "user" if role == "user" else "assistant"
        if isinstance(content, str):
            if content.strip():
                turns.append(Turn(MESSAGE, actor, role=role, text=content, timestamp=ts))
            continue
        for b in content or []:
            bt = b.get("type")
            if bt == "text" and (b.get("text") or "").strip():
                turns.append(Turn(MESSAGE, actor, role=role, text=b["text"], timestamp=ts))
            elif bt == "thinking":
                turns.append(Turn(REASONING, "assistant", role="assistant",
                                  text=b.get("thinking") or b.get("text"), timestamp=ts))
            elif bt == "tool_use":
                tool_by_id[b.get("id")] = b.get("name")
                turns.append(Turn(TOOL_CALL, "assistant", role="assistant", tool_name=b.get("name"),
                                  tool_input=b.get("input"), timestamp=ts, meta={"id": b.get("id")}))
            elif bt == "tool_result":
                name = tool_by_id.get(b.get("tool_use_id"), "tool")
                turns.append(Turn(TOOL_RESULT, name, role="tool", tool_name=name,
                                  tool_result=b.get("content"), is_error=bool(b.get("is_error")),
                                  timestamp=ts, meta={"id": b.get("tool_use_id")}))
    return turns


# --- adapters ----------------------------------------------------------------

def tau_bench(rec: Dict[str, Any]) -> UTrajectory:
    system, turns = _openai_turns(rec.get("traj", []))
    return UTrajectory(
        source="sierra-research/tau-bench",
        id=f"task{rec.get('task_id')}-trial{rec.get('trial')}",
        subject=_first_user_text(turns) or f"task {rec.get('task_id')}",
        turns=turns, system=system,
        outcome={"reward": rec.get("reward")},
        metadata={"info": rec.get("info")},
    )


def swe_rebench(rec: Dict[str, Any]) -> UTrajectory:
    system, turns = _openai_turns(rec.get("trajectory", []))
    return UTrajectory(
        source="nebius/SWE-rebench-openhands-trajectories",
        id=rec.get("trajectory_id") or rec.get("instance_id"),
        subject=rec.get("instance_id") or "",
        turns=turns, system=system, tools=rec.get("tools"),
        outcome={"resolved": rec.get("resolved"), "exit_status": rec.get("exit_status")},
        metadata={"repo": rec.get("repo"), "instance_id": rec.get("instance_id")},
    )


def agent_traces(rec: Dict[str, Any]) -> UTrajectory:
    turns = _anthropic_turns(rec.get("trace", []))
    system = None
    for m in rec.get("messages", []):
        if m.get("role") == "system" and m.get("content"):
            system = m["content"]
            break
    return UTrajectory(
        source="trace-commons/agent-traces",
        id=rec.get("session_id") or "",
        subject=_excerpt(rec.get("prompt")),
        turns=turns, created_at=_parse_dt(rec.get("sent_at")),
        system=system, tools=rec.get("tools"),
        metadata={"harness": rec.get("harness"),
                  "num_user_messages": rec.get("num_user_messages"),
                  "num_tool_calls": rec.get("num_tool_calls")},
    )


_TOOL_CALL_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)
_TOOL_RESP_RE = re.compile(r"<tool_response>\s*(\{.*?\})\s*</tool_response>", re.DOTALL)


def hermes(rec: Dict[str, Any]) -> UTrajectory:
    system: Optional[str] = None
    turns: List[Turn] = []
    for c in rec.get("conversations", []):
        who, value = c.get("from"), c.get("value") or ""
        if who == "system":
            system = value
        elif who == "human":
            turns.append(Turn(MESSAGE, "user", role="user", text=value))
        elif who == "gpt":
            text = _TOOL_CALL_RE.sub("", value).strip()
            if text:
                turns.append(Turn(MESSAGE, "assistant", role="assistant", text=text))
            for m in _TOOL_CALL_RE.findall(value):  # multiple => parallel tool calls
                o = _maybe_json(m) or {}
                turns.append(Turn(TOOL_CALL, "assistant", role="assistant",
                                  tool_name=o.get("name"), tool_input=o.get("arguments")))
        elif who == "tool":
            for m in _TOOL_RESP_RE.findall(value):
                o = _maybe_json(m) or {}
                name = o.get("name") or "tool"
                turns.append(Turn(TOOL_RESULT, name, role="tool", tool_name=name,
                                  tool_result=o.get("content")))
    return UTrajectory(
        source="NousResearch/hermes-function-calling-v1",
        id=rec.get("id") or "",
        subject=_first_user_text(turns) or (rec.get("task") or ""),
        turns=turns, system=system, tools=_maybe_json(rec.get("tools")),
        metadata={"category": rec.get("category"), "subcategory": rec.get("subcategory")},
    )


def mind2web(rec: Dict[str, Any]) -> UTrajectory:
    turns: List[Turn] = [Turn(MESSAGE, "user", role="user", text=rec.get("confirmed_task") or "")]
    reprs = rec.get("action_reprs") or []
    for i, act in enumerate(rec.get("actions") or []):
        dom = act.get("cleaned_html")
        if dom:
            turns.append(Turn(OBSERVATION, "environment", role="environment", text=dom))
        op = act.get("operation") or {}
        target = None
        pos = act.get("pos_candidates") or []
        if pos:
            target = {k: pos[0].get(k) for k in ("tag", "backend_node_id") if pos[0].get(k) is not None}
        turns.append(Turn(ACTION, "assistant", role="assistant",
                          tool_name=op.get("op"),
                          tool_input={"op": op.get("op"), "value": op.get("value"), "target": target},
                          text=reprs[i] if i < len(reprs) else None,
                          meta={"action_uid": act.get("action_uid")}))
    return UTrajectory(
        source="osunlp/Mind2Web",
        id=rec.get("annotation_id") or "",
        subject=_excerpt(rec.get("confirmed_task")),
        turns=turns,
        metadata={"website": rec.get("website"), "domain": rec.get("domain"),
                  "subdomain": rec.get("subdomain")},
    )


def api_bank(turn_dicts: List[Dict[str, Any]], traj_id: str) -> UTrajectory:
    turns: List[Turn] = []
    for t in turn_dicts:
        role = t.get("role")
        if role == "User":
            turns.append(Turn(MESSAGE, "user", role="user", text=t.get("text")))
        elif role == "AI":
            if t.get("text"):
                turns.append(Turn(MESSAGE, "assistant", role="assistant", text=t.get("text")))
        elif role == "API":
            name = t.get("api_name") or "api"
            turns.append(Turn(TOOL_CALL, "assistant", role="assistant",
                              tool_name=name, tool_input=t.get("param_dict")))
            res = t.get("result") or {}
            exc = res.get("exception") if isinstance(res, dict) else None
            turns.append(Turn(TOOL_RESULT, name, role="tool", tool_name=name,
                              tool_result=res, is_error=bool(exc)))
    return UTrajectory(
        source="liminghao1630/API-Bank",
        id=traj_id,
        subject=_first_user_text(turns),
        turns=turns,
    )


_WW_HANDOFF_RE = re.compile(r"^(.+?)\s*\(->\s*(.+?)\)\s*$")
_WW_THOUGHT_RE = re.compile(r"^(.+?)\s*\(thought\)\s*$")


def who_and_when(rec: Dict[str, Any]) -> UTrajectory:
    """Kevin355/Who_and_When (Magentic-One multi-agent logs). Roles encode the
    speaking agent and delegations, e.g. `Orchestrator (-> WebSurfer)`.

    NOTE: agent->agent delegations are emitted as HANDOFF turns, which the
    converter maps onto vCon's `transfer` dialog type BY CONVENTION (not an
    IETF-defined mapping). See docs/conventions.md.
    """
    turns: List[Turn] = []
    for h in rec.get("history", []):
        role = (h.get("role") or "").strip()
        content = h.get("content") or ""
        if role in ("human", "user"):
            if content.strip():
                turns.append(Turn(MESSAGE, "user", role="user", text=content))
            continue
        mo = _WW_HANDOFF_RE.match(role)
        if mo:
            frm, to = mo.group(1).strip(), mo.group(2).strip()
            if content.strip():
                turns.append(Turn(MESSAGE, frm, role="agent", text=content))
            turns.append(Turn(HANDOFF, frm, role="agent", handoff_to=to))
            continue
        mt = _WW_THOUGHT_RE.match(role)
        if mt:
            turns.append(Turn(REASONING, mt.group(1).strip(), role="agent", text=content))
            continue
        turns.append(Turn(MESSAGE, role or "assistant", role="agent", text=content))
    return UTrajectory(
        source="Kevin355/Who_and_When",
        id=rec.get("question_ID") or "",
        subject=_excerpt(rec.get("question")),
        turns=turns,
        outcome={"mistake_agent": rec.get("mistake_agent"),
                 "mistake_step": rec.get("mistake_step"),
                 "is_corrected": rec.get("is_corrected")},
        metadata={"mistake_reason": rec.get("mistake_reason"),
                  "mistake_type": rec.get("mistake_type")},
    )


def _unflatten_indexed(attrs: Dict[str, Any], prefix: str) -> List[Dict[str, Any]]:
    """Collapse OpenInference dotted/indexed keys (`prefix.0.message.role`, ...)
    into an ordered list of nested dicts."""
    out: Dict[int, Dict[str, Any]] = {}
    plen = len(prefix) + 1
    for k, v in attrs.items():
        if not k.startswith(prefix + "."):
            continue
        rest = k[plen:]
        i_str, _, tail = rest.partition(".")
        if not i_str.isdigit():
            continue
        out.setdefault(int(i_str), {})[tail] = v
    return [out[i] for i in sorted(out)]


def openinference(spans: List[Dict[str, Any]], traj_id: str) -> UTrajectory:
    """A list of OpenInference/Phoenix spans sharing a trace -> UTrajectory.

    Spans form a tree; we order by start_time and flatten. To avoid the
    full-history duplication each LLM span carries, we take input messages only
    from the first span and output messages from every span. Span ids are kept in
    Turn.meta so the tree stays recoverable.
    """
    spans = sorted(spans, key=lambda s: s.get("start_time") or "")
    turns: List[Turn] = []
    seeded_input = False
    for s in spans:
        attrs = s.get("attributes") or {}
        ts = s.get("start_time")
        ctx = s.get("context") or {}
        meta = {"span_id": ctx.get("span_id"), "parent_id": s.get("parent_id"),
                "span_kind": s.get("span_kind")}

        in_msgs = _unflatten_indexed(attrs, "llm.input_messages")
        out_msgs = _unflatten_indexed(attrs, "llm.output_messages")

        if not seeded_input and in_msgs:
            for m in in_msgs:
                role = m.get("message.role", "user")
                text = m.get("message.content")
                if text:
                    turns.append(Turn(MESSAGE, "user" if role == "user" else "assistant",
                                      role=role, text=text, timestamp=ts, meta=meta))
            seeded_input = True

        for m in out_msgs:
            text = m.get("message.content")
            if text:
                turns.append(Turn(MESSAGE, "assistant", role="assistant", text=text,
                                  timestamp=ts, meta=meta))
            names = _unflatten_indexed(m, "message.tool_calls")
            for tc in names:
                fn = tc.get("tool_call.function.name")
                if fn:
                    turns.append(Turn(TOOL_CALL, "assistant", role="assistant", tool_name=fn,
                                      tool_input=_maybe_json(tc.get("tool_call.function.arguments")),
                                      timestamp=ts, meta=meta))

        if s.get("span_kind") == "TOOL" or attrs.get("tool.name"):
            name = attrs.get("tool.name") or "tool"
            turns.append(Turn(TOOL_CALL, "assistant", role="assistant", tool_name=name,
                              tool_input=_maybe_json(attrs.get("tool.parameters") or attrs.get("input.value")),
                              timestamp=ts, meta=meta))
            if attrs.get("output.value") is not None:
                turns.append(Turn(TOOL_RESULT, name, role="tool", tool_name=name,
                                  tool_result=_maybe_json(attrs["output.value"]), timestamp=ts, meta=meta))
        elif not in_msgs and not out_msgs and attrs.get("output.value") is not None:
            # Generic span with only input/output values.
            if attrs.get("input.value") is not None:
                turns.append(Turn(OBSERVATION, "environment", role="environment",
                                  text=str(attrs["input.value"]), timestamp=ts, meta=meta))
            turns.append(Turn(MESSAGE, "assistant", role="assistant",
                              text=str(attrs["output.value"]), timestamp=ts, meta=meta))

    return UTrajectory(
        source="arize-ai/openinference",
        id=traj_id,
        subject=f"trace {traj_id}",
        turns=turns,
    )
