"""Anthropic Claude Code session JSONL -> UTrajectory.

Native records (one JSON object per line): `user` / `assistant` / `system` /
`attachment` / `queue-operation` / `file-history-snapshot` ..., linked by
`uuid` / `parentUuid`, with Anthropic Messages-API content blocks
(`text`, `thinking`, `redacted_thinking`, `tool_use`, `tool_result`) inside
`message.content`. `isSidechain` records belong to a sub-agent.

One streamed assistant message is split across several records that repeat the
same `message.id` and `usage`; usage is attached to the first record only so
token counts are not multiplied.
"""
from __future__ import annotations

import json
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

from ..ir import (MAIN, MESSAGE, REASONING, SYSTEM, TOOL_CALL, TOOL_RESULT,
                  ChildSession, Turn, UTrajectory)

SOURCE_DEFAULT = "claude_code"


def _usage(u: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not u:
        return None
    # Anthropic reports `input_tokens` EXCLUDING cache reads/writes. OpenAI/Codex, ATIF and OTel
    # GenAI all define input as INCLUDING cached tokens, so normalize to the inclusive convention.
    read, write = u.get("cache_read_input_tokens") or 0, u.get("cache_creation_input_tokens") or 0
    inp = u.get("input_tokens")
    return {"input": (inp or 0) + read + write if inp is not None else None,
            "output": u.get("output_tokens"), "cached": u.get("cache_read_input_tokens"),
            "cache_write": u.get("cache_creation_input_tokens")}


def _result_text(content: Any) -> Any:
    if isinstance(content, list):
        parts = [b.get("text") for b in content if isinstance(b, dict) and b.get("type") == "text"]
        if len(parts) == len(content):
            return "\n".join(p or "" for p in parts)
    return content


def parse(records: Iterable[Dict[str, Any]], source: str = SOURCE_DEFAULT,
          id: Optional[str] = None) -> UTrajectory:
    records = list(records)
    parent_of = {r["uuid"]: r.get("parentUuid") for r in records if r.get("uuid")}
    mapped = {r["uuid"] for r in records if r.get("uuid") and r.get("type") in ("user", "assistant", "system")}
    relinked = 0

    def nearest_mapped(pid: Optional[str]) -> Optional[str]:
        """Skipped records (attachments, snapshots, ...) are not entries; re-link to the nearest mapped ancestor."""
        seen = set()
        while pid and pid not in mapped and pid not in seen:
            seen.add(pid)
            pid = parent_of.get(pid)
        return pid if pid in mapped else None

    turns: List[Turn] = []
    seen_msg: set = set()
    models: List[str] = []
    skipped: Counter = Counter()
    child: Dict[str, ChildSession] = {}
    sid = cwd = branch = version = None

    for r in records:
        typ = r.get("type")
        sid = sid or r.get("sessionId")
        cwd = cwd or r.get("cwd")
        branch = branch or r.get("gitBranch")
        version = version or r.get("version")
        session = MAIN
        if r.get("isSidechain"):
            session = f"sidechain:{r.get('agentId') or 'agent'}"
            child.setdefault(session, ChildSession(parent=MAIN, agent_session_id=r.get("agentId")))
        pid = nearest_mapped(r.get("parentUuid"))
        relinked += pid != r.get("parentUuid")
        common = dict(timestamp=r.get("timestamp"), entry_id=r.get("uuid"), parent_id=pid, session=session)
        msg = r.get("message") or {}
        content = msg.get("content")

        if typ == "user":
            if isinstance(content, str):
                turns.append(Turn(MESSAGE, "user", role="user", text=content, **common))
            for b in content if isinstance(content, list) else []:
                bt = b.get("type")
                if bt == "text":
                    turns.append(Turn(MESSAGE, "user", role="user", text=b.get("text", ""), **common))
                elif bt == "tool_result":
                    err = b.get("is_error")
                    turns.append(Turn(TOOL_RESULT, "assistant", tool_result=_result_text(b.get("content")),
                                      call_id=b.get("tool_use_id"), is_error=bool(err) if err is not None else None,
                                      status=("error" if err else "success"), **common))
                else:
                    skipped[f"user.{bt}"] += 1
        elif typ == "assistant":
            model = msg.get("model")
            if model and model != "<synthetic>" and model not in models:
                models.append(model)
            mid = msg.get("id")
            usage = None
            if mid and mid not in seen_msg:
                seen_msg.add(mid)
                usage = _usage(msg.get("usage"))
            blocks = content if isinstance(content, list) else []
            if usage and not any(b.get("type") == "text" for b in blocks):
                # Dialog.token_usage needs a message; thinking/tool_use-only turns would lose their usage.
                turns.append(Turn(SYSTEM, "assistant", event_type="token-count",
                                  data={**{k: v for k, v in usage.items() if v is not None}, "model": model},
                                  **common))
                usage = None
            for b in blocks:
                bt = b.get("type")
                if bt == "thinking":
                    th = b.get("thinking") or ""
                    # `signature` is an integrity token for replaying thinking to the API, not
                    # ciphertext of the content, so it is NOT mapped to `encrypted`.
                    if not th:
                        skipped["thinking.signature_only(empty content)"] += 1
                    turns.append(Turn(REASONING, "assistant", text=th, **common))
                elif bt == "redacted_thinking":
                    turns.append(Turn(REASONING, "assistant", text="", encrypted=b.get("data"), **common))
                elif bt == "text":
                    turns.append(Turn(MESSAGE, "assistant", text=b.get("text", ""), model=model,
                                      usage=usage, **common))
                    usage = None
                elif bt == "tool_use":
                    turns.append(Turn(TOOL_CALL, "assistant", tool_name=b.get("name"),
                                      tool_input=b.get("input"), call_id=b.get("id"), **common))
                else:
                    skipped[f"assistant.{bt}"] += 1
        elif typ == "system":
            data = {k: r[k] for k in ("subtype", "content", "level", "durationMs") if k in r}
            turns.append(Turn(SYSTEM, "assistant", event_type=r.get("subtype") or "system", data=data or None,
                              **common))
        else:
            skipped[typ or "unknown"] += 1

    sid = id or sid or "unknown"
    meta = {"harness": "claude_code", "native_records_not_mapped": dict(skipped) or None,
            "parent_id_relinked": relinked or None}
    return UTrajectory(
        source=source, id=sid, turns=turns,
        subject=next((t.text[:80] for t in turns if t.kind == MESSAGE and t.role == "user" and t.text), sid),
        agent_meta={"model_id": models[0], "model_provider": "anthropic", "models": models,
                    "cli_name": "claude-code", "cli_version": version} if models else None,
        environment={"working_dir": cwd} if cwd else None,
        vcs={"type": "git", "branch": branch} if branch else None,
        agent_session_id=sid, format="interactive", child_sessions=child, metadata=meta,
    )


def parse_jsonl(text: str, **kw: Any) -> UTrajectory:
    return parse((json.loads(l) for l in text.splitlines() if l.strip()), **kw)
