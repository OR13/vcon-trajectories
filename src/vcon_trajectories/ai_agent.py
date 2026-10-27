"""IR -> vCon `ai_agent` extension (draft-birkholz-vcon-ai-agent-extension).

Mapping (draft section in parentheses):

- user / agent(s)           -> `parties[]` (person / bot); `agent_meta` on the agent (Party params)
- one agent session         -> `sessions[]` Session Object + `agent_session_id`,
                               `format`, `environment` (Session params)
- sub-agent / sidechain     -> additional Session, referenced from the parent with
                               Session_Reference type "child" (Session params)
- message                   -> `dialog[]` "text" Dialog + `model_id`, `token_usage`,
                               `entry_id`, `parent_id` (Dialog params)
- tool call / result        -> `events[]` "tool-call" / "tool-result" (Event types)
- reasoning / thinking      -> `events[]` "reasoning" (`encrypted` when opaque)
- lifecycle & anything the
  draft has no type for     -> `events[]` "system-event" (vendor `event_type`)
- system prompt, tool defs  -> `attachments[]` (core)
- outcome / corpus metadata -> `analysis[]` report (core)

Timestamps: Events REQUIRE `time`. Turns without a native timestamp get a
monotonic synthetic one and the vCon says so in its analysis report.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .attribution import file_attribution
from .ir import (ACTION, HANDOFF, INCOMPLETE, MAIN, MESSAGE, OBSERVATION,
                 REASONING, SYSTEM, TOOL_CALL, TOOL_RESULT, Turn, UTrajectory)

RECORDER = {"name": "vcon-trajectories", "version": "0.2.0"}
DEFAULT_CREATED_AT = datetime(2026, 10, 26, tzinfo=timezone.utc)
_USAGE_KEYS = ("input", "output", "cached", "cache_write", "reasoning", "total")


def deterministic_uuid8(key: str) -> str:
    """Reproducible RFC 9562 UUIDv8 derived from `key` (stable vCon uuids -> clean diffs)."""
    h = bytearray(hashlib.sha256(key.encode("utf-8")).digest()[:16])
    h[6] = (h[6] & 0x0F) | 0x80
    h[8] = (h[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(h)))


def _parse(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def _fmt(dt: datetime) -> str:
    s = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    if dt.microsecond // 1000:  # millisecond resolution; sub-ms remainders are dropped, not shown as ".000"
        s += f".{dt.microsecond // 1000:03d}"
    return s + "Z"


def _usage(u: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not u:
        return None
    out: Dict[str, Any] = {}
    for k in _USAGE_KEYS:
        v = u.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
            out[k] = int(v)
    if isinstance(u.get("cost"), (int, float)) and u["cost"] >= 0:
        out["cost"] = u["cost"]
    return out or None


def _actor(t: Turn) -> str:
    """Events are attributed to an agent party; tools/environments are not parties."""
    if t.role in ("tool", "environment") or t.actor == "user":
        return "assistant"
    return t.actor


def _clean(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def utrajectory_to_vcon(ut: UTrajectory) -> Dict[str, Any]:
    first_ts = next((_parse(t.timestamp) for t in ut.turns if _parse(t.timestamp)), None)
    base = ut.created_at or first_ts or DEFAULT_CREATED_AT
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)

    # ---- parties -----------------------------------------------------------
    parties: List[Dict[str, Any]] = [{"type": "person", "name": "user"}]
    pidx: Dict[str, int] = {"user": 0}

    def party(actor: str) -> int:
        if actor not in pidx:
            pidx[actor] = len(parties)
            parties.append({"type": "bot", "name": actor})
        return pidx[actor]

    for t in ut.turns:  # create in first-seen order so the primary agent is party 1
        if t.kind == MESSAGE and t.role == "user":
            continue
        party(_actor(t))
    if len(parties) == 1:
        party("assistant")
    am = ut.agent_meta
    if am and am.get("model_id") and am.get("model_provider"):
        parties[1]["agent_meta"] = _clean(dict(am))

    # ---- sessions ----------------------------------------------------------
    skeys = [MAIN] + [k for k in ut.child_sessions if k != MAIN]
    for t in ut.turns:
        if t.session not in skeys:
            skeys.append(t.session)
    sidx = {k: i for i, k in enumerate(skeys)}

    synthesized = 0

    def time_of(i: int, t: Turn) -> str:
        nonlocal synthesized
        dt = _parse(t.timestamp)
        if dt is None:
            synthesized += 1
            dt = base + timedelta(seconds=i)
        return _fmt(dt)

    dialog: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []
    sess_dialog: Dict[str, List[int]] = {k: [] for k in skeys}
    sess_parties: Dict[str, List[int]] = {k: [] for k in skeys}
    sess_times: Dict[str, List[datetime]] = {k: [] for k in skeys}

    for i, t in enumerate(ut.turns):
        when = time_of(i, t)
        sess_times[t.session].append(_parse(when))
        s = sidx[t.session]
        a = party(_actor(t))
        for p in ([0, a] if t.role == "user" else [a]):
            if p not in sess_parties[t.session]:
                sess_parties[t.session].append(p)
        native = _clean({"entry_id": t.entry_id, "parent_id": t.parent_id})

        if t.kind == MESSAGE:
            speaker = 0 if t.role == "user" else a
            d = _clean({
                "type": "text", "start": when, "parties": speaker,
                "mediatype": t.mediatype or "text/plain", "encoding": "none",
                "body": t.text or "",
                "model_id": t.model if speaker != 0 else None,
                "token_usage": _usage(t.usage) if speaker != 0 else None,
                **native,
            })
            dialog.append(d)
            sess_dialog[t.session].append(len(dialog) - 1)
            continue

        ev: Dict[str, Any]
        if t.kind in (TOOL_CALL, ACTION):
            ev = {"type": "tool-call", "time": when, "session": s, "party": a,
                  "tool_name": t.tool_name or "unknown",
                  "input": t.tool_input if t.tool_input is not None else {},
                  **_clean({"call_id": t.call_id})}
        elif t.kind in (TOOL_RESULT, OBSERVATION):
            out = t.tool_result if t.kind == TOOL_RESULT else t.text
            ev = {"type": "tool-result", "time": when, "session": s, "party": a,
                  "output": out if out is not None else "",
                  **_clean({"call_id": t.call_id, "status": t.status, "is_error": t.is_error})}
        elif t.kind == REASONING:
            ev = {"type": "reasoning", "time": when, "session": s, "party": a,
                  "content": t.text if t.text is not None else "",
                  **_clean({"encrypted": t.encrypted, "subject": t.subject})}
        elif t.kind == HANDOFF:
            ev = {"type": "system-event", "time": when, "session": s, "party": a,
                  "event_type": "agent-handoff",
                  "data": {"from": t.actor, "to": t.handoff_to}}
        elif t.kind == INCOMPLETE:
            ev = {"type": "system-event", "time": when, "session": s, "party": a,
                  "event_type": "run-incomplete",
                  "data": _clean({"disposition": t.disposition or "failed", "reason": t.text})}
        else:  # SYSTEM
            ev = {"type": "system-event", "time": when, "session": s, "party": a,
                  "event_type": t.event_type or "system",
                  **({"data": t.data} if t.data else {})}
        ev.update(native)
        events.append(ev)

    sessions: List[Dict[str, Any]] = []
    for k in skeys:
        times = sorted(x for x in sess_times[k] if x)
        sd = _clean({
            "start": _fmt(times[0]) if times else _fmt(base),
            "duration": round((times[-1] - times[0]).total_seconds(), 3) if len(times) > 1 else None,
            "parties": sess_parties[k] or [0, 1],
            "dialog": sess_dialog[k] or None,
        })
        if k == MAIN:
            sd.update(_clean({"agent_session_id": ut.agent_session_id, "format": ut.format,
                              "environment": ut.environment}))
        else:
            cs = ut.child_sessions.get(k)
            if cs and cs.agent_session_id:
                sd["agent_session_id"] = cs.agent_session_id
        sessions.append(sd)
    for k, cs in ut.child_sessions.items():
        if k not in sidx:
            continue
        ref = _clean({"session": sidx[k], "type": "child", "description": cs.description})
        sessions[sidx[cs.parent if cs.parent in sidx else MAIN]].setdefault("sessions", []).append(ref)

    # ---- assemble ----------------------------------------------------------
    vcon: Dict[str, Any] = {
        "uuid": deterministic_uuid8(f"{ut.source}#{ut.id}"),
        "extensions": ["ai_agent"],
        "created_at": _fmt(base),
        "subject": ut.subject or ut.id,
        "recording_agent": dict(RECORDER),
    }
    if ut.vcs:
        vcon["vcs"] = dict(ut.vcs)
    fa, fa_stats = file_attribution(ut) if ut.file_edits else (None, {})
    if fa:
        vcon["file_attribution"] = fa
    vcon.update({"sessions": sessions, "parties": parties})
    if events:
        vcon["events"] = events
    if dialog:
        vcon["dialog"] = dialog

    attachments: List[Dict[str, Any]] = []
    start0 = sessions[0]["start"]
    if ut.system:
        attachments.append({"purpose": "system-prompt", "start": start0, "party": 1, "session": 0,
                            "mediatype": "text/plain", "encoding": "none", "body": ut.system})
    if ut.tools:
        attachments.append({"purpose": "tool-definitions", "start": start0, "party": 1, "session": 0,
                            "mediatype": "application/json", "encoding": "json", "body": ut.tools})
    if attachments:
        vcon["attachments"] = attachments

    report = {k: v for k, v in {**ut.metadata, **ut.outcome, "source": ut.source, "id": ut.id,
                                "timestamps_synthesized": synthesized or None,
                                **({f"file_attribution_{k}": v for k, v in fa_stats.items()} if fa_stats else {})}.items()
              if v is not None}
    vcon["analysis"] = [{"type": "report", "vendor": ut.source, "schema": "trajectory-metadata",
                         "session": list(range(len(sessions))), "mediatype": "application/json",
                         "encoding": "json", "body": report}]
    return vcon
