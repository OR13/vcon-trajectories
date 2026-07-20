"""Shared intermediate representation for agent trajectories, and the single
IR -> vCon 0.4.0 (core) converter used by every source adapter.

A trajectory is a `UTrajectory`: metadata + an ordered list of `Turn`s. Each Turn
is one atomic event (a message, a tool call, a tool result, a reasoning step, or a
GUI action/observation). The converter maps:

- distinct actors      -> `parties[]` (user=person, agents/tools=bot)
- each Turn            -> a `dialog[]` entry (reasoning -> `analysis` instead)
- reasoning traces     -> `analysis` (schema `chain-of-thought`)
- outcome / metadata   -> `analysis` (type `report`)
- system prompt        -> `attachments` (purpose `system-prompt`)
- tool definitions     -> `attachments` (purpose `tool-definitions`)

Real per-turn timestamps are used when a Turn carries one; otherwise a monotonic
offset from `created_at` is synthesized.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..convert import DEFAULT_CREATED_AT, _ts, deterministic_uuid8

# Turn kinds
MESSAGE = "message"
TOOL_CALL = "tool_call"
TOOL_RESULT = "tool_result"
REASONING = "reasoning"
ACTION = "action"           # GUI/environment action taken by the agent
OBSERVATION = "observation"  # environment state returned to the agent


@dataclass
class Turn:
    kind: str
    actor: str                       # party label, e.g. "user", "assistant", "web_search"
    role: str = "assistant"          # semantic role: user|assistant|system|tool|agent|environment
    text: Optional[str] = None       # message/reasoning/observation content
    tool_name: Optional[str] = None
    tool_input: Any = None
    tool_result: Any = None
    is_error: bool = False
    timestamp: Optional[str] = None  # RFC3339, if the source carries one
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UTrajectory:
    source: str                      # dataset id (attribution + uuid namespace)
    id: str
    subject: str = ""
    turns: List[Turn] = field(default_factory=list)
    created_at: Optional[datetime] = None
    system: Optional[str] = None
    tools: Any = None                # raw tool definitions (kept verbatim)
    outcome: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


def _person_or_bot(role: str) -> str:
    return "person" if role == "user" else "bot"


def _base_time(ut: UTrajectory) -> datetime:
    if ut.created_at:
        return ut.created_at if ut.created_at.tzinfo else ut.created_at.replace(tzinfo=timezone.utc)
    for t in ut.turns:
        if t.timestamp:
            try:
                dt = datetime.fromisoformat(t.timestamp.replace("Z", "+00:00"))
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                pass
    return DEFAULT_CREATED_AT


def utrajectory_to_vcon(ut: UTrajectory) -> Dict[str, Any]:
    base = _base_time(ut)

    parties: List[Dict[str, Any]] = []
    idx: Dict[str, int] = {}

    def party(actor: str, role: str) -> int:
        if actor not in idx:
            idx[actor] = len(parties)
            parties.append({"type": _person_or_bot(role), "name": actor})
        return idx[actor]

    user_idx = party("user", "user")
    # Primary assistant: first agent-ish actor encountered (lazily created).
    primary_assistant = [None]  # type: List[Optional[int]]

    def assistant_index(actor: str) -> int:
        i = party(actor, "assistant")
        if primary_assistant[0] is None:
            primary_assistant[0] = i
        return i

    dialog: List[Dict[str, Any]] = []
    analysis: List[Dict[str, Any]] = []
    pending_reasoning: List[str] = []

    def start_for(turn: Turn) -> str:
        if turn.timestamp:
            try:
                dt = datetime.fromisoformat(turn.timestamp.replace("Z", "+00:00"))
                dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            except Exception:
                pass
        return _ts(base, len(dialog))

    def add_dialog(**kw: Any) -> int:
        dialog.append(kw)
        i = len(dialog) - 1
        # Attach any buffered reasoning to the dialog it precedes.
        while pending_reasoning:
            analysis.append({
                "type": "report",
                "vendor": ut.source,
                "schema": "chain-of-thought",
                "dialog": [i],
                "mediatype": "text/plain",
                "body": pending_reasoning.pop(0),
                "encoding": "none",
            })
        return i

    for turn in ut.turns:
        if turn.kind == REASONING:
            if turn.text:
                pending_reasoning.append(turn.text)
            continue

        if turn.kind == TOOL_CALL:
            a = assistant_index(turn.actor if turn.role == "agent" else "assistant")
            t = party(turn.tool_name or "tool", "tool")
            add_dialog(
                type="text", parties=[a, t], originator=a,
                start=start_for(turn), application=turn.tool_name,
                mediatype="application/json",
                body={"tool": turn.tool_name, "input": turn.tool_input, **({"id": turn.meta["id"]} if turn.meta.get("id") else {})},
                encoding="json",
            )
        elif turn.kind == TOOL_RESULT:
            t = party(turn.tool_name or "tool", "tool")
            a = primary_assistant[0] if primary_assistant[0] is not None else assistant_index("assistant")
            body = {"content": turn.tool_result}
            if turn.is_error:
                body["is_error"] = True
            add_dialog(
                type="text", parties=[t, a], originator=t,
                start=start_for(turn), application=turn.tool_name,
                mediatype="application/json", body=body, encoding="json",
            )
        elif turn.kind == ACTION:
            a = assistant_index(turn.actor if turn.role == "agent" else "assistant")
            env = party("environment", "environment")
            add_dialog(
                type="text", parties=[a, env], originator=a,
                start=start_for(turn), application=turn.tool_name,
                mediatype="application/json",
                body={"action": turn.tool_name, "input": turn.tool_input, **({"repr": turn.text} if turn.text else {})},
                encoding="json",
            )
        elif turn.kind == OBSERVATION:
            env = party("environment", "environment")
            a = primary_assistant[0] if primary_assistant[0] is not None else assistant_index("assistant")
            add_dialog(
                type="text", parties=[env, a], originator=env,
                start=start_for(turn), mediatype="text/plain",
                body=turn.text or "", encoding="none",
            )
        else:  # MESSAGE
            if turn.role == "user":
                o = user_idx
                other = primary_assistant[0] if primary_assistant[0] is not None else assistant_index("assistant")
            else:
                o = assistant_index(turn.actor if turn.role == "agent" else "assistant")
                other = user_idx
            add_dialog(
                type="text", parties=[o, other], originator=o,
                start=start_for(turn), mediatype="text/plain",
                body=turn.text or "", encoding="none",
            )

    # Flush any trailing reasoning onto the last dialog entry.
    if pending_reasoning and dialog:
        last = len(dialog) - 1
        for r in pending_reasoning:
            analysis.append({
                "type": "report", "vendor": ut.source, "schema": "chain-of-thought",
                "dialog": [last], "mediatype": "text/plain", "body": r, "encoding": "none",
            })

    # Outcome + metadata report.
    report_body = {k: v for k, v in {**ut.metadata, **ut.outcome, "source": ut.source, "id": ut.id}.items() if v is not None}
    analysis.append({
        "type": "report", "vendor": ut.source, "schema": "trajectory-metadata",
        "dialog": list(range(len(dialog))), "mediatype": "application/json",
        "body": report_body, "encoding": "json",
    })

    attachments: List[Dict[str, Any]] = []
    if ut.system:
        attachments.append({
            "purpose": "system-prompt", "start": _ts(base, 0),
            "party": primary_assistant[0] if primary_assistant[0] is not None else user_idx,
            "dialog": 0, "mediatype": "text/plain", "body": ut.system, "encoding": "none",
        })
    if ut.tools:
        attachments.append({
            "purpose": "tool-definitions", "start": _ts(base, 0),
            "party": primary_assistant[0] if primary_assistant[0] is not None else user_idx,
            "dialog": 0, "mediatype": "application/json", "body": ut.tools, "encoding": "json",
        })

    vcon: Dict[str, Any] = {
        "vcon": "0.4.0",
        "uuid": deterministic_uuid8(f"{ut.source}#{ut.id}"),
        "created_at": _ts(base, 0),
        "subject": ut.subject or ut.id,
        "parties": parties,
        "dialog": dialog,
        "analysis": analysis,
    }
    if attachments:
        vcon["attachments"] = attachments
    return vcon
