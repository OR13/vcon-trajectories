"""vCon `ai_agent` -> ATIF (Harbor's Agent Trajectory Interchange Format, v1.8).

ATIF is step-oriented (one step per user message, system prompt, or agent turn);
the vCon form is split across `dialog[]` and `events[]`. `timeline()` merges the
two into one order and `to_atif()` folds that order into steps:

- user Dialog                    -> step(source=user)
- assistant Dialog / reasoning   -> step(source=agent): message / reasoning_content
- tool-call                      -> step.tool_calls[]
- tool-result                    -> step.observation.results[] (matched by call_id)
- token-count system-event       -> metrics of the preceding agent step
- other system-events            -> step(source=system) with the event in `extra`
- child Sessions                 -> subagent_trajectories[] (embedded form)

ATIF has no tool-error flag, so `is_error`/`status` ride in the observation
result's `extra`. `token_usage.input` is read as INCLUDING cached tokens, which
is ATIF's `prompt_tokens` definition (the draft does not say; see draft-feedback).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "ATIF-v1.8"
_SPAWN_TOOLS = ("Task", "Agent")
# Tie-break for entries with identical timestamps: think -> say -> act -> observe.
_RANK = {"reasoning": 0, "dialog": 1, "tool-call": 2, "tool-result": 3}


def _t(s: Optional[str]) -> datetime:
    try:
        d = datetime.fromisoformat((s or "").replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def timeline(vcon: Dict[str, Any], session: Optional[int] = None) -> List[Tuple[str, Dict[str, Any]]]:
    """Dialog and events of `vcon` (optionally one session) in a single deterministic order.

    The draft defines no total order across the two arrays, so order is
    (time, think/say/act/observe rank, original position).
    """
    sessions = vcon.get("sessions", [])
    in_session = None
    if session is not None:
        in_session = set(sessions[session].get("dialog", []))
    items: List[Tuple[datetime, int, int, str, Dict[str, Any]]] = []
    for i, d in enumerate(vcon.get("dialog", [])):
        if in_session is not None and i not in in_session:
            continue
        items.append((_t(d.get("start")), _RANK["dialog"], i, "dialog", d))
    for i, e in enumerate(vcon.get("events", [])):
        if session is not None and e.get("session") != session:
            continue
        items.append((_t(e.get("time")), _RANK.get(e["type"], 4), 1_000_000 + i, e["type"], e))
    items.sort(key=lambda x: x[:3])
    return [(k, o) for _, _, _, k, o in items]


def _is_user(vcon: Dict[str, Any], d: Dict[str, Any]) -> bool:
    p = d.get("parties")
    p = p[0] if isinstance(p, list) and p else p
    return isinstance(p, int) and vcon["parties"][p].get("type") == "person"


def _text(v: Any) -> str:
    return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str)


def _metrics(u: Dict[str, Any]) -> Dict[str, Any]:
    m: Dict[str, Any] = {}
    if u.get("input") is not None:
        m["prompt_tokens"] = u["input"]
    if u.get("output") is not None:
        m["completion_tokens"] = u["output"]
    if u.get("cached") is not None:
        m["cached_tokens"] = u["cached"]
    if u.get("cost") is not None:
        m["cost_usd"] = u["cost"]
    extra = {k: u[k] for k in ("reasoning", "cache_write", "total") if u.get(k) is not None}
    if extra:
        m["extra"] = extra
    return m


def _add_metrics(step: Dict[str, Any], u: Dict[str, Any]) -> None:
    new = _metrics(u)
    cur = step.setdefault("metrics", {})
    for k, v in new.items():
        if k == "extra":
            ex = cur.setdefault("extra", {})
            for kk, vv in v.items():
                ex[kk] = ex.get(kk, 0) + vv
        elif isinstance(v, (int, float)):
            cur[k] = cur.get(k, 0) + v
    if not cur:
        step.pop("metrics")


def _tool_defs(vcon: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    for a in vcon.get("attachments", []):
        if a.get("purpose") != "tool-definitions" or not isinstance(a.get("body"), list):
            continue
        out = []
        for t in a["body"]:
            if not isinstance(t, dict):
                continue
            if t.get("type") == "function" and isinstance(t.get("function"), dict):
                out.append(t)
            elif t.get("name"):  # Anthropic-style {name, description, input_schema}
                out.append({"type": "function", "function": {
                    "name": t["name"], "description": t.get("description", ""),
                    "parameters": t.get("input_schema") or t.get("parameters") or {"type": "object"}}})
        return out or None
    return None


def _trajectory(vcon: Dict[str, Any], session: int, traj_id: str, children: Dict[int, Dict[str, Any]],
                notes: List[str]) -> Dict[str, Any]:
    parties = vcon["parties"]
    bot = next((p for p in parties if p.get("type") == "bot"), {})
    meta = bot.get("agent_meta") or {}
    steps: List[Dict[str, Any]] = []
    call_step: Dict[str, Dict[str, Any]] = {}
    spawn_calls: List[Tuple[Dict[str, Any], str]] = []
    cur: Optional[Dict[str, Any]] = None  # open agent step
    synthesized_ids = 0

    sysprompt = next((a["body"] for a in vcon.get("attachments", [])
                      if a.get("purpose") == "system-prompt" and session == 0), None)
    start = vcon["sessions"][session]["start"]
    if isinstance(sysprompt, str):
        steps.append({"timestamp": start, "source": "system", "message": sysprompt})

    def agent_step(ts: str, model: Optional[str]) -> Dict[str, Any]:
        nonlocal cur
        if cur is None:
            cur = {"timestamp": ts, "source": "agent", "message": ""}
            steps.append(cur)
        if model and "model_name" not in cur:
            cur["model_name"] = model
        return cur

    for kind, o in timeline(vcon, session):
        if kind == "dialog":
            if _is_user(vcon, o):
                cur = None
                steps.append({"timestamp": o["start"], "source": "user", "message": _text(o.get("body", ""))})
                continue
            if cur is not None and (cur.get("message") or cur.get("tool_calls")):
                cur = None
            st = agent_step(o["start"], o.get("model_id"))
            st["message"] = _text(o.get("body", ""))
            if o.get("token_usage"):
                _add_metrics(st, o["token_usage"])
        elif kind == "reasoning":
            if cur is not None and (cur.get("message") or cur.get("tool_calls")):
                cur = None
            st = agent_step(o["time"], None)
            blocks = st.setdefault("extra", {}).setdefault("vcon_reasoning", [])
            blocks.append({k: o[k] for k in ("content", "encrypted") if o.get(k)})
            if o.get("content"):
                st["reasoning_content"] = (st["reasoning_content"] + "\n\n" if "reasoning_content" in st else "") + o["content"]
        elif kind == "tool-call":
            st = agent_step(o["time"], None)
            cid = o.get("call_id")
            if not cid:
                synthesized_ids += 1
                cid = f"vcon-call-{synthesized_ids}"
            args = o.get("input")
            st.setdefault("tool_calls", []).append({
                "tool_call_id": cid, "function_name": o["tool_name"],
                "arguments": args if isinstance(args, dict) else {"value": args}})
            call_step[cid] = st
            if o["tool_name"] in _SPAWN_TOOLS:
                spawn_calls.append((st, cid))
        elif kind == "tool-result":
            cid = o.get("call_id")
            st = call_step.get(cid) if cid else None
            if st is None:
                st = agent_step(o["time"], None)
            res: Dict[str, Any] = {"content": _text(o.get("output", ""))}
            if cid and cid in call_step:
                res["source_call_id"] = cid
            flags = {k: o[k] for k in ("is_error", "status") if k in o}
            if flags:
                res["extra"] = flags
            st.setdefault("observation", {"results": []})["results"].append(res)
            cur = None  # next reasoning/message starts a new step
        elif kind == "system-event":
            et = o.get("event_type", "system-event")
            if et == "token-count" and isinstance(o.get("data"), dict):
                target = cur if cur is not None else next((s for s in reversed(steps) if s["source"] == "agent"), None)
                if target is not None:
                    _add_metrics(target, o["data"])
                    continue
            steps.append({"timestamp": o["time"], "source": "system", "message": et,
                          "extra": {"event_type": et, **({"data": o["data"]} if o.get("data") else {})}})

    # child sessions: ordered match against spawning Task/Agent calls
    refs = vcon["sessions"][session].get("sessions", [])
    for n, ref in enumerate(r for r in refs if r.get("type") == "child"):
        child = children.get(ref["session"])
        if child is None:
            continue
        sref = {"trajectory_id": child["trajectory_id"],
                **({"session_id": child["session_id"]} if child.get("session_id") else {})}
        if n < len(spawn_calls):
            st, cid = spawn_calls[n]
            res = next((r for r in st.get("observation", {}).get("results", []) if r.get("source_call_id") == cid), None)
            if res is None:
                res = {"source_call_id": cid}
                st.setdefault("observation", {"results": []})["results"].append(res)
            res.setdefault("subagent_trajectory_ref", []).append(sref)
        else:
            notes.append(f"child session {ref['session']} could not be matched to a Task/Agent call; "
                         "vCon Session_Reference carries no call_id")
            steps.append({"timestamp": child["steps"][0]["timestamp"] if child["steps"] else start,
                          "source": "system", "message": "subagent-delegation",
                          "observation": {"results": [{"subagent_trajectory_ref": [sref]}]}})

    for s in steps:
        blocks = (s.get("extra") or {}).get("vcon_reasoning")
        if blocks is not None and len(blocks) == 1 and list(blocks[0]) == ["content"]:
            del s["extra"]["vcon_reasoning"]  # reasoning_content already carries it losslessly
            if not s["extra"]:
                del s["extra"]
    for i, s in enumerate(steps, 1):
        s["step_id"] = i
        if s["source"] != "agent":
            s.pop("model_name", None)
        s = {k: s[k] for k in ("step_id", "timestamp", "source", "model_name", "message", "reasoning_content",
                               "tool_calls", "observation", "metrics", "extra") if k in s}
        steps[i - 1] = s

    sd = vcon["sessions"][session]
    agent: Dict[str, Any] = {"name": meta.get("cli_name") or bot.get("name") or "unknown",
                             "version": str(meta.get("cli_version") or "unknown")}
    if meta.get("model_id"):
        agent["model_name"] = meta["model_id"]
    if meta:
        agent["extra"] = {"agent_meta": meta}
    tdefs = _tool_defs(vcon) if session == 0 else None
    if tdefs:
        agent["tool_definitions"] = tdefs
    extra = {k: v for k, v in {"environment": sd.get("environment"), "format": sd.get("format"),
                               "vcs": vcon.get("vcs") if session == 0 else None}.items() if v}
    t: Dict[str, Any] = {"schema_version": SCHEMA_VERSION}
    if sd.get("agent_session_id"):
        t["session_id"] = sd["agent_session_id"]
    t.update({"trajectory_id": traj_id, "agent": agent, "steps": steps})
    pt = sum(s.get("metrics", {}).get("prompt_tokens", 0) for s in steps)
    ct = sum(s.get("metrics", {}).get("completion_tokens", 0) for s in steps)
    cc = sum(s.get("metrics", {}).get("cached_tokens", 0) for s in steps)
    cost = sum(s.get("metrics", {}).get("cost_usd", 0) for s in steps)
    fm = {k: v for k, v in {"total_prompt_tokens": pt, "total_completion_tokens": ct,
                            "total_cached_tokens": cc, "total_cost_usd": cost or None,
                            "total_steps": len(steps)}.items() if v is not None}
    if pt or ct:
        t["final_metrics"] = fm
    if extra:
        t["extra"] = extra
    return t


def to_atif(vcon: Dict[str, Any]) -> Dict[str, Any]:
    """Convert an `ai_agent` vCon into one ATIF trajectory (children embedded)."""
    notes: List[str] = []
    n = len(vcon.get("sessions", []))
    children: Dict[int, Dict[str, Any]] = {}
    for i in range(1, n):
        child = _trajectory(vcon, i, f"{vcon['uuid']}#session-{i}", {}, notes)
        if child["steps"]:  # ATIF requires >= 1 step; a Session with no entries has nothing to embed
            children[i] = child
        else:
            notes.append(f"session {i} has no dialog or events, not embedded")
    root = _trajectory(vcon, 0, f"{vcon['uuid']}", children, notes)
    if children:
        root["subagent_trajectories"] = [children[i] for i in sorted(children)]
    if vcon.get("subject"):
        notes.insert(0, f"vCon subject: {vcon['subject']}")
    notes.append(f"converted from vCon {vcon['uuid']} (ai_agent extension) by vcon-trajectories")
    root["notes"] = "; ".join(notes)
    return root
