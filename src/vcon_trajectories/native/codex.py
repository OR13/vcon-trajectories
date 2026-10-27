"""OpenAI Codex CLI rollout JSONL -> UTrajectory.

Native lines: `session_meta`, `turn_context`, `response_item` (Responses-API items:
`message`, `reasoning`, `function_call`, `function_call_output`, ...) and
`event_msg` (`user_message`, `agent_message`, `token_count`, `exec_command_end`,
`task_started`, `task_complete`, ...).

`response_item` is canonical for model I/O. `event_msg` `user_message` /
`agent_message` duplicate response_item messages and are skipped; `exec_command_end`
supplies exit codes for the matching function_call_output; `token_count` becomes a
`token-count` system-event.
"""
from __future__ import annotations

import json
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

import re

from ..ir import MESSAGE, REASONING, SYSTEM, TOOL_CALL, TOOL_RESULT, FileEdit, Hunk, Turn, UTrajectory

SOURCE_DEFAULT = "codex"
_INJECTED = ("<environment_context>", "# AGENTS.md", "<user_instructions>", "<permissions instructions>")


def _text(content: Any) -> str:
    if isinstance(content, list):
        return "\n".join(c.get("text", "") for c in content if isinstance(c, dict))
    return content or ""


def _maybe_json(s: Any) -> Any:
    if isinstance(s, str):
        try:
            return json.loads(s)
        except ValueError:
            return s
    return s


_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def _unified(diff: str) -> List[Hunk]:
    hunks: List[Hunk] = []
    for line in diff.split("\n"):
        m = _HUNK.match(line)
        if m:
            hunks.append(Hunk(int(m[1]), int(m[2] or 1), int(m[3]), int(m[4] or 1), []))
        elif hunks and line[:1] in (" ", "-", "+"):
            hunks[-1].lines.append(line)
    return hunks


def parse(records: Iterable[Dict[str, Any]], source: str = SOURCE_DEFAULT,
          id: Optional[str] = None) -> UTrajectory:
    recs = list(records)
    exits: Dict[str, Dict[str, Any]] = {}
    for r in recs:
        p = r.get("payload") or {}
        if r.get("type") == "event_msg" and p.get("type") == "exec_command_end":
            exits[p.get("call_id")] = p

    turns: List[Turn] = []
    edits: List[FileEdit] = []
    call_turn: Dict[str, int] = {}
    skipped: Counter = Counter()
    meta: Dict[str, Any] = {}
    model = None
    last_user = False

    for r in recs:
        typ, p, ts = r.get("type"), r.get("payload") or {}, r.get("timestamp")
        if typ == "session_meta":
            meta = p
        elif typ == "turn_context":
            model = model or p.get("model")
        elif typ == "response_item":
            pt = p.get("type")
            if pt == "message":
                role, text = p.get("role"), _text(p.get("content"))
                if role == "developer" or text.lstrip().startswith(_INJECTED):
                    turns.append(Turn(SYSTEM, "assistant", timestamp=ts,
                                      event_type="developer-instructions" if role == "developer" else "context-injection",
                                      data={"role": role, "content": text}))
                elif role == "user":
                    turns.append(Turn(MESSAGE, "user", role="user", text=text, timestamp=ts))
                else:
                    turns.append(Turn(MESSAGE, "assistant", text=text, model=model, timestamp=ts))
            elif pt == "reasoning":
                summ = "\n".join(s.get("text", "") for s in (p.get("summary") or []) if isinstance(s, dict))
                body = _text(p.get("content")) if p.get("content") else summ
                turns.append(Turn(REASONING, "assistant", text=body, encrypted=p.get("encrypted_content"),
                                  timestamp=ts))
            elif pt in ("function_call", "custom_tool_call", "local_shell_call"):
                args = p.get("arguments") if pt == "function_call" else (p.get("input") or p.get("action"))
                call_turn[p.get("call_id") or p.get("id")] = len(turns)
                turns.append(Turn(TOOL_CALL, "assistant", tool_name=p.get("name") or pt,
                                  tool_input=_maybe_json(args), call_id=p.get("call_id") or p.get("id"),
                                  timestamp=ts))
            elif pt in ("function_call_output", "custom_tool_call_output"):
                ex = exits.get(p.get("call_id"))
                code = ex.get("exit_code") if ex else None
                out = p.get("output")
                turns.append(Turn(TOOL_RESULT, "assistant", tool_result=_maybe_json(out) if not isinstance(out, str) else out,
                                  call_id=p.get("call_id"), timestamp=ts,
                                  is_error=(code != 0) if code is not None else None,
                                  status=("success" if code == 0 else "error") if code is not None else None))
            else:
                skipped[f"response_item.{pt}"] += 1
        elif typ == "event_msg":
            et = p.get("type")
            if et == "token_count" and p.get("info"):
                last = p["info"].get("last_token_usage") or {}
                turns.append(Turn(SYSTEM, "assistant", timestamp=ts, event_type="token-count", data={
                    "input": last.get("input_tokens"), "cached": last.get("cached_input_tokens"),
                    "output": last.get("output_tokens"), "reasoning": last.get("reasoning_output_tokens"),
                    "total": last.get("total_tokens")}))
            elif et == "patch_apply_end" and p.get("success") and p.get("call_id") in call_turn:
                for path, ch in (p.get("changes") or {}).items():
                    k, ti = ch.get("type"), call_turn[p["call_id"]]
                    if k == "update" and ch.get("unified_diff"):
                        edits.append(FileEdit(path, "update", ti, model, hunks=_unified(ch["unified_diff"]), call_id=p["call_id"]))
                    elif k == "add" and isinstance(ch.get("content"), str):
                        edits.append(FileEdit(path, "create", ti, model, content=ch["content"], call_id=p["call_id"]))
                    elif k == "delete":
                        edits.append(FileEdit(path, "delete", ti, model, call_id=p["call_id"]))
            elif et in ("task_started", "task_complete", "turn_aborted"):
                turns.append(Turn(SYSTEM, "assistant", timestamp=ts, event_type=et.replace("_", "-"),
                                  data={k: v for k, v in p.items() if k != "type" and k != "last_agent_message"} or None))
            elif et in ("user_message", "agent_message", "exec_command_end", "token_count"):
                skipped[f"event_msg.{et}(dup/empty)"] += 1
            else:
                skipped[f"event_msg.{et}"] += 1
        else:
            skipped[typ or "unknown"] += 1

    sid = id or meta.get("id") or "unknown"
    git = meta.get("git") or {}
    first_user = next((t.text for t in turns if t.kind == MESSAGE and t.role == "user" and t.text), sid)
    return UTrajectory(
        source=source, id=sid, turns=turns, subject=first_user[:80],
        system=meta.get("base_instructions", {}).get("text") if isinstance(meta.get("base_instructions"), dict) else meta.get("instructions"),
        agent_meta={"model_id": model, "model_provider": meta.get("model_provider") or "openai",
                    "cli_name": "codex-cli", "cli_version": meta.get("cli_version")} if model else None,
        environment={"working_dir": meta["cwd"]} if meta.get("cwd") else None,
        vcs=({"type": "git", **{k: v for k, v in {"revision": git.get("commit_hash"), "branch": git.get("branch"),
                                                   "repository": git.get("repository_url")}.items() if v}} if git else None),
        agent_session_id=sid, format="interactive", file_edits=edits,
        metadata={"harness": "codex", "originator": meta.get("originator"),
                  "native_records_not_mapped": dict(skipped) or None},
    )


def parse_jsonl(text: str, **kw: Any) -> UTrajectory:
    return parse((json.loads(l) for l in text.splitlines() if l.strip()), **kw)
