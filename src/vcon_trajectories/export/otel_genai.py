"""vCon `ai_agent` -> OpenTelemetry GenAI spans (semantic-conventions-genai, status: Development).

Span tree, built from the ATIF step structure so both exporters agree on ordering:

    invoke_agent {agent}                  gen_ai.operation.name=invoke_agent, gen_ai.conversation.id
      chat {model}                        one per agent step; usage + gen_ai.output.messages
        execute_tool {tool}               one per tool call; arguments, result, error.type

Output is a plain list of span dicts (OTLP/JSON-like: ids as hex, times in unix nanos,
attributes as a flat map) rather than a protobuf payload. `gen_ai.output.messages` is the
JSON string the conventions prescribe (parts of type text / reasoning / tool_call);
`gen_ai.tool.call.arguments` / `.result` are opt-in in the spec because they can hold
sensitive data, and are emitted here because the point is a lossless trajectory.
`gen_ai.input.messages` is not reconstructed: the vCon stores each message once, not the
re-sent history of every model call.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .atif import to_atif

PROVIDERS = (("claude", "anthropic"), ("gpt", "openai"), ("o1", "openai"), ("o3", "openai"),
             ("o4", "openai"), ("codex", "openai"), ("gemini", "gcp.gemini"))


def provider_of(model: Optional[str], meta: Optional[Dict[str, Any]] = None) -> Optional[str]:
    if meta and meta.get("model_provider"):
        p = meta["model_provider"]
        return {"google": "gcp.gemini"}.get(p, p)
    m = (model or "").lower()
    return next((p for k, p in PROVIDERS if m.startswith(k)), None)


def _id(key: str, nbytes: int) -> str:
    return hashlib.sha256(key.encode()).hexdigest()[: nbytes * 2]


def _ns(ts: Optional[str]) -> Optional[int]:
    try:
        d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    d = d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    return int(d.timestamp() * 1e9)


def _attrs(**kw: Any) -> Dict[str, Any]:
    return {k: v for k, v in kw.items() if v is not None}


def _spans_for(traj: Dict[str, Any], trace_id: str, parent: Optional[str]) -> List[Dict[str, Any]]:
    agent = traj["agent"]
    steps = traj["steps"]
    provider = provider_of(agent.get("model_name"), (agent.get("extra") or {}).get("agent_meta")) or "unknown"
    root_id = _id(trace_id + traj["trajectory_id"], 8)
    first = next((_ns(s.get("timestamp")) for s in steps if _ns(s.get("timestamp"))), 0)
    last = max([_ns(s.get("timestamp")) or 0 for s in steps] + [first])
    fm = traj.get("final_metrics") or {}
    spans: List[Dict[str, Any]] = [{
        "trace_id": trace_id, "span_id": root_id, "parent_span_id": parent,
        "name": f"invoke_agent {agent['name']}", "kind": "INTERNAL",
        "start_time_unix_nano": first, "end_time_unix_nano": last, "status": {"code": "UNSET"},
        "attributes": _attrs(**{
            "gen_ai.operation.name": "invoke_agent", "gen_ai.agent.name": agent["name"],
            "gen_ai.agent.version": agent["version"], "gen_ai.conversation.id": traj.get("session_id"),
            "gen_ai.provider.name": provider, "gen_ai.request.model": agent.get("model_name"),
            "gen_ai.usage.input_tokens": fm.get("total_prompt_tokens"),
            "gen_ai.usage.output_tokens": fm.get("total_completion_tokens"),
            "gen_ai.usage.cache_read.input_tokens": fm.get("total_cached_tokens")})}]
    for i, s in enumerate(steps):
        if s["source"] != "agent":
            continue
        t0 = _ns(s.get("timestamp")) or first
        nxt = next((_ns(x.get("timestamp")) for x in steps[i + 1:] if _ns(x.get("timestamp"))), None)
        t1 = max(nxt or t0, t0)
        parts: List[Dict[str, Any]] = []
        if s.get("reasoning_content"):
            parts.append({"type": "reasoning", "content": s["reasoning_content"]})
        if s.get("message"):
            parts.append({"type": "text", "content": s["message"]})
        for c in s.get("tool_calls", []):
            parts.append({"type": "tool_call", "id": c["tool_call_id"], "name": c["function_name"],
                          "arguments": c["arguments"]})
        m = s.get("metrics") or {}
        ex = m.get("extra") or {}
        model = s.get("model_name") or agent.get("model_name")
        chat_id = _id(f"{trace_id}{traj['trajectory_id']}chat{s['step_id']}", 8)
        spans.append({
            "trace_id": trace_id, "span_id": chat_id, "parent_span_id": root_id,
            "name": f"chat {model}" if model else "chat", "kind": "CLIENT",
            "start_time_unix_nano": t0, "end_time_unix_nano": t1, "status": {"code": "UNSET"},
            "attributes": _attrs(**{
                "gen_ai.operation.name": "chat", "gen_ai.provider.name": provider_of(model) or provider,  # Required; "unknown" when the vCon has no model
                "gen_ai.request.model": model, "gen_ai.conversation.id": traj.get("session_id"),
                "gen_ai.usage.input_tokens": m.get("prompt_tokens"),
                "gen_ai.usage.output_tokens": m.get("completion_tokens"),
                "gen_ai.usage.cache_read.input_tokens": m.get("cached_tokens"),
                "gen_ai.usage.cache_write.input_tokens": ex.get("cache_write"),
                "gen_ai.response.finish_reasons": ["tool_call"] if s.get("tool_calls") else None,
                "gen_ai.output.messages": json.dumps(
                    [{"role": "assistant", "parts": parts}], ensure_ascii=False) if parts else None})})
        results = {r.get("source_call_id"): r for r in (s.get("observation") or {}).get("results", [])}
        for c in s.get("tool_calls", []):
            r = results.get(c["tool_call_id"])
            rx = (r or {}).get("extra") or {}
            failed = rx.get("is_error") is True
            spans.append({
                "trace_id": trace_id, "span_id": _id(f"{trace_id}{traj['trajectory_id']}tool{s['step_id']}/{c['tool_call_id']}", 8),
                "parent_span_id": chat_id, "name": f"execute_tool {c['function_name']}", "kind": "INTERNAL",
                "start_time_unix_nano": t0, "end_time_unix_nano": t1,
                "status": {"code": "ERROR"} if failed else {"code": "UNSET"},
                "attributes": _attrs(**{
                    "gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": c["function_name"],
                    "gen_ai.tool.call.id": c["tool_call_id"],
                    "gen_ai.tool.call.arguments": json.dumps(c["arguments"], ensure_ascii=False),
                    "gen_ai.tool.call.result": r.get("content") if r else None,
                    "error.type": "tool_error" if failed else None})})
            for ref in (r or {}).get("subagent_trajectory_ref", []):
                spans[-1].setdefault("links_trajectory_id", []).append(ref["trajectory_id"])
    return spans


def to_otel(vcon: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Span list for the whole vCon. Embedded subagent trajectories become `invoke_agent`
    spans parented to the `execute_tool` span that spawned them (spec: the sub-agent's
    invoke_agent span MAY be a child of the parent's execute_tool span)."""
    atif = to_atif(vcon)
    trace_id = _id(vcon["uuid"], 16)
    spans = _spans_for(atif, trace_id, None)
    by_traj = {s["trajectory_id"]: s for s in atif.get("subagent_trajectories", [])}
    for tid, sub in by_traj.items():
        parent = next((sp["span_id"] for sp in spans if tid in sp.get("links_trajectory_id", [])),
                      spans[0]["span_id"])
        spans += _spans_for(sub, trace_id, parent)
    for sp in spans:
        sp.pop("links_trajectory_id", None)
    return spans
