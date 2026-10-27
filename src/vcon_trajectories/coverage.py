"""Which draft constructs does a vCon actually exercise? (used for the corpus report)"""
from __future__ import annotations

from typing import Any, Dict, Set

FEATURES = [
    ("dialog.text", "message as Dialog"),
    ("dialog.model_id", "Dialog.model_id"),
    ("dialog.token_usage", "Dialog.token_usage"),
    ("dialog.entry_id", "Dialog.entry_id / parent_id"),
    ("event.tool-call", "tool-call event"),
    ("event.tool-result", "tool-result event"),
    ("tool.call_id_paired", "call_id pairs call<->result"),
    ("tool.parallel_calls", "parallel tool calls"),
    ("tool.is_error", "tool-result is_error=true"),
    ("tool.subagent_spawn", "sub-agent spawn call (Task/Agent tool)"),
    ("event.reasoning", "reasoning event"),
    ("reasoning.encrypted", "reasoning.encrypted"),
    ("event.system-event", "system-event"),
    ("event.entry_id", "Event.entry_id / parent_id"),
    ("party.agent_meta", "Party.agent_meta"),
    ("session.environment", "Session.environment"),
    ("session.agent_session_id", "Session.agent_session_id"),
    ("session.child", "child Session (sub-agent)"),
    ("vcon.vcs", "vcs"),
    ("vcon.file_attribution", "file_attribution"),
    ("file_attribution.multi_model", "file_attribution per-range contributor (mixed models)"),
    ("attachment.tools", "tool definitions (attachment)"),
    ("time.synthesized", "timestamps synthesized (NOT native)"),
]


def features(v: Dict[str, Any]) -> Set[str]:
    f: Set[str] = set()
    for d in v.get("dialog", []):
        f.add("dialog.text")
        for k in ("model_id", "token_usage"):
            if k in d:
                f.add(f"dialog.{k}")
        if "entry_id" in d:
            f.add("dialog.entry_id")
    calls, results, run, best = set(), set(), 0, 0
    for e in v.get("events", []):
        f.add(f"event.{e['type']}")
        if "entry_id" in e:
            f.add("event.entry_id")
        if e["type"] == "tool-call":
            run += 1
            best = max(best, run)
            if "call_id" in e:
                calls.add(e["call_id"])
            if e.get("tool_name") in ("Task", "Agent"):
                f.add("tool.subagent_spawn")
        else:
            run = 0
        if e["type"] == "tool-result":
            if "call_id" in e:
                results.add(e["call_id"])
            if e.get("is_error"):
                f.add("tool.is_error")
        if e["type"] == "reasoning" and "encrypted" in e:
            f.add("reasoning.encrypted")
    if calls & results:
        f.add("tool.call_id_paired")
    if best >= 2:
        f.add("tool.parallel_calls")
    if any("agent_meta" in p for p in v.get("parties", [])):
        f.add("party.agent_meta")
    for s in v.get("sessions", []):
        for k in ("environment", "agent_session_id"):
            if k in s:
                f.add(f"session.{k}")
        if s.get("sessions"):
            f.add("session.child")
    if "vcs" in v:
        f.add("vcon.vcs")
    fa = v.get("file_attribution")
    if fa:
        f.add("vcon.file_attribution")
        if any("contributor" in r for fl in fa["files"] for c in fl["conversations"] for r in c["ranges"]):
            f.add("file_attribution.multi_model")
    if any(a.get("purpose") == "tool-definitions" for a in v.get("attachments", [])):
        f.add("attachment.tools")
    for a in v.get("analysis", []):
        if isinstance(a.get("body"), dict) and a["body"].get("timestamps_synthesized"):
            f.add("time.synthesized")
    return f
