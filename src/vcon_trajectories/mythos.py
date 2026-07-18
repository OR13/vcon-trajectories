"""Convert the structured ``VINAY-UMRETHE/Mythos-Agent`` HF dataset to vCons.

This dataset is a **gated** Hugging Face dataset (CC-BY-4.0) of agent
trajectories in the Anthropic Messages shape: each row has a ``system`` prompt,
a list of ``tools`` (full JSON-schema definitions), and ``messages`` whose
``content`` is either a plain string or a list of ``text`` / ``tool_use`` /
``tool_result`` blocks.

Unlike the Qwythos markdown logs, this source is structured (non-lossy to parse)
and carries a real per-record ``created_at``. One row → one vCon v0.4.0.

Loading requires an authorized ``HF_TOKEN`` (see docs/data-source.md). Because
the source is gated, callers should treat the generated vCons as gated too.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .convert import _ts, deterministic_uuid8

DATASET_REPO = "VINAY-UMRETHE/Mythos-Agent"
_PARQUET = "data/train-00000-of-00001.parquet"

_USER = 0
_AGENT = 1


def load_records(token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Download the gated parquet and return rows as dicts (requires access)."""
    from huggingface_hub import hf_hub_download
    import pyarrow.parquet as pq

    path = hf_hub_download(
        repo_id=DATASET_REPO,
        filename=_PARQUET,
        repo_type="dataset",
        token=token if token else True,
    )
    return pq.read_table(path).to_pylist()


def _decode(content: Any) -> Any:
    """messages[].content is JSON-encoded: decode to a str or a list of blocks."""
    if isinstance(content, str):
        try:
            return json.loads(content)
        except Exception:
            return content
    return content


def _base_time(rec: Dict[str, Any]) -> datetime:
    ts = rec.get("created_at")
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return datetime(1970, 1, 1, tzinfo=timezone.utc)


def _subject(rec: Dict[str, Any]) -> str:
    md = rec.get("metadata") or {}
    first_user = ""
    for m in rec.get("messages") or []:
        if m.get("role") == "user":
            c = _decode(m.get("content"))
            if isinstance(c, str):
                first_user = c
                break
    cat = f"[{md.get('category')}] " if md.get("category") else ""
    return f"{cat}{' '.join(first_user.split())[:80]}".strip() or (md.get("slug") or rec.get("id", ""))


def record_to_vcon(rec: Dict[str, Any]) -> Dict[str, Any]:
    model = rec.get("model_target") or "mythos"
    base = _base_time(rec)

    parties: List[Dict[str, Any]] = [
        {"type": "person", "name": "user"},
        {"type": "bot", "name": model},
    ]
    tool_party: Dict[str, int] = {}

    def tool_index(name: str) -> int:
        if name not in tool_party:
            tool_party[name] = len(parties)
            parties.append({"type": "bot", "name": name})
        return tool_party[name]

    dialog: List[Dict[str, Any]] = []

    def add_dialog(**kw: Any) -> int:
        kw["start"] = _ts(base, len(dialog))
        dialog.append(kw)
        return len(dialog) - 1

    last_tool: Optional[str] = None
    for m in rec.get("messages") or []:
        role = m.get("role")
        content = _decode(m.get("content"))
        speaker = _USER if role == "user" else _AGENT
        listener = _AGENT if role == "user" else _USER

        if isinstance(content, str):
            add_dialog(
                type="text",
                parties=[speaker, listener],
                originator=speaker,
                mediatype="text/plain",
                body=content,
                encoding="none",
            )
            continue

        for block in content:
            btype = block.get("type")
            if btype == "text":
                add_dialog(
                    type="text",
                    parties=[speaker, listener],
                    originator=speaker,
                    mediatype="text/plain",
                    body=block.get("text", ""),
                    encoding="none",
                )
            elif btype == "tool_use":
                name = block.get("name") or "tool"
                last_tool = name
                ti = tool_index(name)
                add_dialog(
                    type="text",
                    parties=[_AGENT, ti],
                    originator=_AGENT,
                    application=name,
                    mediatype="application/json",
                    body={"id": block.get("id"), "name": name, "input": block.get("input")},
                    encoding="json",
                )
            elif btype == "tool_result":
                name = last_tool or "tool"
                ti = tool_index(name)
                add_dialog(
                    type="text",
                    parties=[ti, _AGENT],
                    originator=ti,
                    application=name,
                    mediatype="application/json",
                    body={
                        "tool_use_id": block.get("tool_use_id"),
                        "content": block.get("content"),
                        "is_error": block.get("is_error"),
                    },
                    encoding="json",
                )
            else:
                # Unknown block type: preserve it verbatim rather than drop it.
                add_dialog(
                    type="text",
                    parties=[speaker, listener],
                    originator=speaker,
                    mediatype="application/json",
                    body=block,
                    encoding="json",
                )

    md = rec.get("metadata") or {}
    analysis: List[Dict[str, Any]] = [
        {
            "type": "report",
            "vendor": DATASET_REPO,
            "product": model,
            "schema": "mythos-agent-metadata",
            "dialog": list(range(len(dialog))),
            "mediatype": "application/json",
            "body": {
                **md,
                "id": rec.get("id"),
                "model_target": rec.get("model_target"),
                "schema_version": rec.get("schema_version"),
                "dataset_created_at": _ts(base, 0),
            },
            "encoding": "json",
        }
    ]

    attachments: List[Dict[str, Any]] = []
    if rec.get("system"):
        attachments.append(
            {
                "purpose": "system-prompt",
                "start": _ts(base, 0),
                "party": _AGENT,
                "dialog": 0,
                "mediatype": "text/plain",
                "body": rec["system"],
                "encoding": "none",
            }
        )
    if rec.get("tools"):
        attachments.append(
            {
                "purpose": "tool-definitions",
                "start": _ts(base, 0),
                "party": _AGENT,
                "dialog": 0,
                "mediatype": "application/json",
                "body": rec["tools"],
                "encoding": "json",
            }
        )

    vcon: Dict[str, Any] = {
        "vcon": "0.4.0",
        "uuid": deterministic_uuid8(f"{DATASET_REPO}#{rec.get('id')}"),
        "created_at": _ts(base, 0),
        "subject": _subject(rec),
        "parties": parties,
        "dialog": dialog,
        "analysis": analysis,
    }
    if attachments:
        vcon["attachments"] = attachments
    return vcon
