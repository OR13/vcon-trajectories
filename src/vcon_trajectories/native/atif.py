"""ATIF (Harbor, v1.x) -> IR. Lets real Harbor trajectories flow into `ai_agent` vCons
and lets `scripts/fidelity.py` measure the vCon -> ATIF -> vCon round trip.

Mapping:
- step(user)  -> MESSAGE(user); step(system) -> SYSTEM `system-prompt` unless it is `extra.event_type`
- step(agent) -> REASONING (reasoning_content), MESSAGE (message + model + metrics),
                 TOOL_CALL per tool_calls[], TOOL_RESULT per observation.results[]
- metrics     -> usage {input=prompt_tokens, cached, output, + extra}
- subagent_trajectories -> ChildSession (+ turns tagged with the child's session key)
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ..ir import (MAIN, MESSAGE, REASONING, SYSTEM, TOOL_CALL, TOOL_RESULT, ChildSession, Turn,
                  UTrajectory)

SOURCE_DEFAULT = "atif"


def _flat(c: Any) -> Any:
    """ContentPart arrays are flattened to their text; media parts keep a placeholder."""
    if isinstance(c, list):
        return "\n".join(p.get("text") if p.get("type") == "text" else f"[{p.get('type')}: {(p.get('source') or {}).get('path')}]"
                         for p in c if isinstance(p, dict))
    return c


def _usage(m: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not m:
        return None
    ex = m.get("extra") or {}
    u = {"input": m.get("prompt_tokens"), "output": m.get("completion_tokens"), "cached": m.get("cached_tokens"),
         "cost": m.get("cost_usd"), "reasoning": ex.get("reasoning"), "cache_write": ex.get("cache_write"),
         "total": ex.get("total")}
    return {k: v for k, v in u.items() if v is not None} or None


def _steps(t: Dict[str, Any], session: str, turns: List[Turn], default_model: Optional[str],
           prompts: List[str]) -> None:
    for s in t["steps"]:
        ts, src = s.get("timestamp"), s["source"]
        if src == "user":
            turns.append(Turn(MESSAGE, "user", role="user", text=_flat(s.get("message")), timestamp=ts, session=session))
            continue
        if src == "system":
            ex = s.get("extra") or {}
            if "event_type" in ex:
                turns.append(Turn(SYSTEM, "assistant", timestamp=ts, session=session,
                                  event_type=ex["event_type"], data=ex.get("data")))
            elif not s.get("observation"):
                prompts.append(_flat(s.get("message")))
            else:  # v1.2+ system step with an observation (context summarization, delegation, resets)
                refs = [ref for r in s["observation"].get("results", []) for ref in r.get("subagent_trajectory_ref") or []]
                turns.append(Turn(SYSTEM, "assistant", timestamp=ts, session=session,
                                  event_type="subagent-delegation" if refs else "system-step",
                                  data={k: v for k, v in {"message": _flat(s.get("message")),
                                                          "subagent_refs": refs or None}.items() if v}))
            continue
        model = s.get("model_name") or default_model
        blocks = (s.get("extra") or {}).get("vcon_reasoning")
        if blocks is None and s.get("reasoning_content"):
            blocks = [{"content": s["reasoning_content"]}]
        for b in blocks or []:
            turns.append(Turn(REASONING, "assistant", text=b.get("content", ""), encrypted=b.get("encrypted"),
                              timestamp=ts, session=session))
        usage = _usage(s.get("metrics"))
        msg = _flat(s.get("message"))
        if msg or (usage and not s.get("tool_calls")):
            turns.append(Turn(MESSAGE, "assistant", text=msg or "", model=model, usage=usage, timestamp=ts, session=session))
        elif usage:
            turns.append(Turn(SYSTEM, "assistant", timestamp=ts, session=session, event_type="token-count",
                              data={**usage, **({"model": model} if model else {})}))
        for c in s.get("tool_calls") or []:
            turns.append(Turn(TOOL_CALL, "assistant", tool_name=c["function_name"], tool_input=c.get("arguments"),
                              call_id=c["tool_call_id"], timestamp=ts, session=session))
        for r in (s.get("observation") or {}).get("results", []):
            if "content" not in r and (r.get("subagent_trajectory_ref") or "source_call_id" not in r):
                continue  # pure delegation marker: the child session carries the content
            fx = r.get("extra") or {}
            turns.append(Turn(TOOL_RESULT, "assistant", tool_result=_flat(r.get("content", "")),
                              call_id=r.get("source_call_id"), is_error=fx.get("is_error"), status=fx.get("status"),
                              timestamp=ts, session=session))


def parse_trajectory(t: Dict[str, Any], id: Optional[str] = None, source: str = SOURCE_DEFAULT) -> UTrajectory:
    agent = t.get("agent") or {}
    meta = (agent.get("extra") or {}).get("agent_meta")
    if not meta and agent.get("model_name"):
        meta = {"model_id": agent["model_name"], "cli_name": agent.get("name"), "cli_version": agent.get("version")}
    ex = t.get("extra") or {}
    ut = UTrajectory(source=source, id=id or t.get("session_id") or t.get("trajectory_id") or "atif",
                     subject=t.get("notes") or "", agent_meta=meta, agent_session_id=t.get("session_id"),
                     environment=ex.get("environment"), vcs=ex.get("vcs"), format=ex.get("format"),
                     tools=agent.get("tool_definitions"))
    turns: List[Turn] = []
    prompts: List[str] = []
    _steps(t, MAIN, turns, agent.get("model_name"), prompts)
    ut.system = "\n\n".join(prompts) or None
    for sub in t.get("subagent_trajectories") or []:
        key = sub["trajectory_id"]
        ut.child_sessions[key] = ChildSession(parent=MAIN, agent_session_id=sub.get("session_id"),
                                              description=(sub.get("agent") or {}).get("name"))
        _steps(sub, key, turns, (sub.get("agent") or {}).get("model_name"), [])
    ut.turns = turns
    fm = t.get("final_metrics")
    if fm:
        ut.metadata["final_metrics"] = fm
    return ut
