"""Google Gemini CLI sessions (as normalized by SWE-chat / Entire.io) -> UTrajectory.

CAVEAT: this is NOT a raw Gemini CLI log. SWE-chat's `conversations` table holds
one row per turn (`turn_type` = user_prompt / assistant_response / tool_use / ...)
with Gemini-native tool names (`run_shell_command`, `write_file`, `replace`) but
**no tool results**. A raw Gemini CLI / ADK `Event` log parser is future work
(no public raw corpus was found).
"""
from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional

from ..ir import MESSAGE, SYSTEM, TOOL_CALL, Turn, UTrajectory

SOURCE_DEFAULT = "swe-chat/gemini-cli"


def _ts(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).replace(" ", "T", 1)
    return s.replace("+00:00", "Z")


def _int(v: Any) -> Optional[int]:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def parse(rows: Iterable[Dict[str, Any]], source: str = SOURCE_DEFAULT) -> UTrajectory:
    rows = sorted(rows, key=lambda r: int(float(r.get("turn_number") or 0)))
    turns: List[Turn] = []
    models: List[str] = []
    for r in rows:
        tt, ts, tid = r.get("turn_type"), _ts(r.get("timestamp")), r.get("turn_id")
        usage = {"input": _int(r.get("input_tokens")), "output": _int(r.get("output_tokens")),
                 "cached": _int(r.get("cache_read_input_tokens"))}
        if tt == "user_prompt":
            turns.append(Turn(MESSAGE, "user", role="user", text=r.get("content") or "", timestamp=ts, entry_id=tid))
        elif tt == "assistant_response":
            if r.get("model") and r["model"] not in models:
                models.append(r["model"])
            turns.append(Turn(MESSAGE, "assistant", text=r.get("content") or "", timestamp=ts, entry_id=tid,
                              model=r.get("model"), usage={k: v for k, v in usage.items() if v} or None))
        elif tt == "tool_use":
            raw = r.get("tool_input_json") or r.get("content")
            try:
                inp = json.loads(raw)
            except (TypeError, ValueError):
                inp = {"truncated_json": raw}
            turns.append(Turn(TOOL_CALL, "assistant", tool_name=r.get("tool_name"), tool_input=inp,
                              call_id=r.get("tool_call_id"), timestamp=ts, entry_id=tid))
        else:
            turns.append(Turn(SYSTEM, "assistant", timestamp=ts, entry_id=tid, event_type=tt or "unknown",
                              data={"content": r.get("content")}))
    sid = rows[0]["session_id"] if rows else "unknown"
    first = next((t.text for t in turns if t.kind == MESSAGE and t.role == "user"), sid)
    return UTrajectory(
        source=source, id=sid, turns=turns, subject=first[:80],
        agent_meta={"model_id": models[0], "model_provider": "google", "models": models,
                    "cli_name": "gemini-cli"} if models else None,
        agent_session_id=sid, format="interactive",
        metadata={"harness": "gemini_cli", "caveat": "SWE-chat normalized turn rows; no tool results"},
    )
