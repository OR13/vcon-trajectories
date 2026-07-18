"""Convert a normalized :class:`Trajectory` into a vCon v0.4.0 object (dict).

See ``docs/mapping.md`` for the full design. In brief: one trajectory → one
vCon; each event → a ``text`` dialog; reasoning traces and trajectory metadata →
``analysis``; tool definitions → ``attachments``.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from .models import Trajectory

VCON_VERSION = "0.4.0"

# The source eval logs are not per-message timestamped; use the source model
# repo's lastModified as the vCon creation time (documented in docs/mapping.md).
DEFAULT_CREATED_AT = datetime(2026, 7, 14, 12, 41, 41, tzinfo=timezone.utc)

_USER = 0
_AGENT = 1


def deterministic_uuid8(key: str) -> str:
    """A reproducible RFC 9562 version-8 UUID derived from ``key``.

    Reproducible so the same trajectory always yields the same vCon uuid
    (nice for git diffs); version/variant bits set to 8 / RFC 4122 as the draft
    recommends UUIDv8.
    """
    h = bytearray(hashlib.sha256(key.encode("utf-8")).digest()[:16])
    h[6] = (h[6] & 0x0F) | 0x80  # version 8
    h[8] = (h[8] & 0x3F) | 0x80  # variant 10xx (RFC 4122)
    return str(uuid.UUID(bytes=bytes(h)))


def _ts(base: datetime, offset_s: int) -> str:
    dt = (base + timedelta(seconds=offset_s)).astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def trajectory_to_vcon(
    traj: Trajectory, created_at: datetime = DEFAULT_CREATED_AT
) -> Dict[str, Any]:
    parties: List[Dict[str, Any]] = [
        {"type": "person", "name": "user"},
        {"type": "bot", "name": traj.model, "org": "empero-ai"},
    ]
    tool_party: Dict[str, int] = {}
    for tool in traj.tools_used:
        tool_party[tool] = len(parties)
        parties.append({"type": "bot", "name": tool, "org": "empero-ai"})

    dialog: List[Dict[str, Any]] = []
    analysis: List[Dict[str, Any]] = []
    attachments: List[Dict[str, Any]] = []

    def add_dialog(**kw: Any) -> int:
        kw["start"] = _ts(created_at, len(dialog))
        dialog.append(kw)
        return len(dialog) - 1

    def add_reasoning(dialog_idx: int, reasoning: str) -> None:
        if not reasoning:
            return
        analysis.append(
            {
                "type": "report",
                "vendor": "empero-ai",
                "product": traj.model,
                "schema": "chain-of-thought",
                "dialog": [dialog_idx],
                "mediatype": "text/plain",
                "body": reasoning,
                "encoding": "none",
            }
        )

    # 1. The human prompt.
    add_dialog(
        type="text",
        parties=[_USER, _AGENT],
        originator=_USER,
        mediatype="text/plain",
        body=traj.prompt,
        encoding="none",
    )

    # 2. Rounds. Tool-calling rounds emit an assistant call + a tool result;
    #    a terminal round (no tool call) contributes its reasoning to the answer.
    terminal_reasoning: List[str] = []
    for r in traj.rounds:
        if r.tool_call is None:
            if r.reasoning:
                terminal_reasoning.append(r.reasoning)
            continue

        tc = r.tool_call
        tool_idx = tool_party[tc.name]
        call_body: Any = {
            "tool": tc.name,
            "input": tc.input if tc.input is not None else {"_raw_arguments": tc.input_raw},
        }
        call_idx = add_dialog(
            type="text",
            parties=[_AGENT, tool_idx],
            originator=_AGENT,
            application=tc.name,
            mediatype="application/json",
            body=call_body,
            encoding="json",
        )
        add_reasoning(call_idx, r.reasoning)

        result_body: Any = tc.result if tc.result is not None else {"_raw_result": tc.result_raw}
        add_dialog(
            type="text",
            parties=[tool_idx, _AGENT],
            originator=tool_idx,
            application=tc.name,
            mediatype="application/json",
            body=result_body,
            encoding="json",
        )

    # 3. The final answer.
    if traj.final_answer:
        answer_idx = add_dialog(
            type="text",
            parties=[_AGENT, _USER],
            originator=_AGENT,
            mediatype="text/plain",
            body=traj.final_answer,
            encoding="none",
        )
        for reasoning in terminal_reasoning:
            add_reasoning(answer_idx, reasoning)
    elif terminal_reasoning and dialog:
        for reasoning in terminal_reasoning:
            add_reasoning(len(dialog) - 1, reasoning)

    # 4. Trajectory-level eval metadata as an analysis report.
    analysis.append(
        {
            "type": "report",
            "vendor": "empero-ai",
            "product": traj.model,
            "schema": "qwythos-eval",
            "dialog": list(range(len(dialog))),
            "mediatype": "application/json",
            "body": {
                "test_id": traj.test_id,
                "kind": traj.kind,
                "category": traj.category,
                "declared_rounds": traj.n_rounds,
                "duration_s": traj.duration_s,
                "tools_used": traj.tools_used,
                "source_repo": traj.source_repo,
                "source_file": traj.source_file,
            },
            "encoding": "json",
        }
    )

    # 5. Tool definitions (names observed in the trajectory) as an attachment.
    if traj.tools_used:
        attachments.append(
            {
                "purpose": "tool-definitions",
                "start": _ts(created_at, 0),
                "party": _AGENT,
                "dialog": 0,
                "mediatype": "application/json",
                "body": [{"name": t} for t in traj.tools_used],
                "encoding": "json",
            }
        )

    key = f"{traj.source_repo}/{traj.source_file}#{traj.test_id}"
    vcon: Dict[str, Any] = {
        "vcon": VCON_VERSION,
        "uuid": deterministic_uuid8(key),
        "created_at": _ts(created_at, 0),
        "subject": traj.subject,
        "parties": parties,
        "dialog": dialog,
        "analysis": analysis,
    }
    if attachments:
        vcon["attachments"] = attachments
    return vcon
