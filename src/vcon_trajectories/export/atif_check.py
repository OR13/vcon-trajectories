"""Structural checks for an ATIF trajectory, written from the rules in the ATIF RFC (v1.8).

This is NOT Harbor's validator: it re-implements the RFC's stated constraints so the
exporter can be checked without the `harbor` package. Run Harbor's own validator
(`python -m harbor.utils.trajectory_validator`) for the authoritative verdict.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

_SOURCES = {"system", "user", "agent"}
_AGENT_ONLY = ("model_name", "reasoning_effort", "reasoning_content", "tool_calls", "metrics")
_NONNEG_INT = ("prompt_tokens", "completion_tokens", "cached_tokens")


def _ts_ok(s: Any) -> bool:
    try:
        datetime.fromisoformat(s.replace("Z", "+00:00"))
        return True
    except (ValueError, AttributeError):
        return False


def check_atif(t: Dict[str, Any], _embedded: bool = False, _path: str = "$") -> List[str]:
    errs: List[str] = []

    def e(msg: str) -> None:
        errs.append(f"{_path}: {msg}")

    if not str(t.get("schema_version", "")).startswith("ATIF-v"):
        e("schema_version missing/invalid")
    agent = t.get("agent")
    if not isinstance(agent, dict) or not agent.get("name") or not agent.get("version"):
        e("agent.name and agent.version are required")
    if _embedded and not t.get("trajectory_id"):
        e("trajectory_id is required on embedded subagent trajectories")
    steps = t.get("steps")
    if not isinstance(steps, list) or not steps:
        return errs + [f"{_path}: steps must be a non-empty array"]

    embedded = t.get("subagent_trajectories") or []
    ids = [s.get("trajectory_id") for s in embedded]
    if len(ids) != len(set(ids)):
        e("subagent_trajectories trajectory_id values must be unique")

    for i, s in enumerate(steps):
        p = f"{_path}.steps[{i}]"
        if s.get("step_id") != i + 1:
            errs.append(f"{p}: step_id must be sequential from 1 (got {s.get('step_id')})")
        if s.get("source") not in _SOURCES:
            errs.append(f"{p}: source must be one of {sorted(_SOURCES)}")
        if "message" not in s or not isinstance(s["message"], (str, list)):
            errs.append(f"{p}: message is required (string or ContentPart array)")
        if s.get("timestamp") is not None and not _ts_ok(s["timestamp"]):
            errs.append(f"{p}: timestamp is not ISO 8601")
        if s.get("source") != "agent":
            for k in _AGENT_ONLY:
                if k in s:
                    errs.append(f"{p}: {k} is only applicable when source is 'agent'")
        calls = s.get("tool_calls") or []
        call_ids = set()
        for j, c in enumerate(calls):
            if not c.get("tool_call_id") or not c.get("function_name") or not isinstance(c.get("arguments"), dict):
                errs.append(f"{p}.tool_calls[{j}]: tool_call_id, function_name and object arguments are required")
            call_ids.add(c.get("tool_call_id"))
        if len(call_ids) != len(calls):
            errs.append(f"{p}: duplicate tool_call_id within step")
        obs = s.get("observation")
        if obs is not None:
            if not isinstance(obs.get("results"), list):
                errs.append(f"{p}.observation.results is required")
            for j, r in enumerate(obs.get("results") or []):
                sc = r.get("source_call_id")
                if sc is not None and sc not in call_ids:
                    errs.append(f"{p}.observation.results[{j}]: source_call_id {sc!r} matches no tool_call in this step")
                if "content" in r and not isinstance(r["content"], (str, list)):
                    errs.append(f"{p}.observation.results[{j}]: content must be string or array")
                for ref in r.get("subagent_trajectory_ref") or []:
                    tid, path = ref.get("trajectory_id"), ref.get("trajectory_path")
                    if not tid and not path:
                        errs.append(f"{p}.observation.results[{j}]: subagent ref needs trajectory_id or trajectory_path")
                    if tid and not path and tid not in ids:
                        errs.append(f"{p}.observation.results[{j}]: trajectory_id {tid!r} not in subagent_trajectories")
        m = s.get("metrics") or {}
        for k in _NONNEG_INT:
            if k in m and (not isinstance(m[k], int) or m[k] < 0):
                errs.append(f"{p}.metrics.{k} must be a non-negative integer")
        if m.get("cached_tokens", 0) > m.get("prompt_tokens", m.get("cached_tokens", 0)):
            errs.append(f"{p}.metrics: cached_tokens exceeds prompt_tokens (prompt_tokens includes cached)")
    for k, sub in enumerate(embedded):
        errs += check_atif(sub, True, f"{_path}.subagent_trajectories[{k}]")
    return errs
