"""EXPERIMENTAL prototype: shared IR -> VAC record + `agent_session` vCon.

Targets two INDIVIDUAL Internet-Drafts (revision -00, NOT WG-adopted):
  - draft-howe-vcon-agent-session-00        (the `agent_session` vCon extension)
  - draft-birkholz-verifiable-agent-conversations-00 (VAC record; the trace body)

See SPEC.md for the extracted model and exact draft status. This reuses the core
project's intermediate representation (`vcon_trajectories.sources.ir`) as input.

Scope/omissions (honest):
  - Emits the UNSIGNED `verifiable-agent-record`. The `signed-agent-record`
    (COSE_Sign1 / CBOR) is NOT produced here — signing is out of scope for this
    JSON prototype.
  - Field-name casing differs by design between the two drafts: the vCon party
    uses underscores (`model_id`, `provider`); the VAC record uses hyphens
    (`model-id`, `model-provider`). We translate deliberately.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from vcon_trajectories.convert import _ts, deterministic_uuid8
from vcon_trajectories.sources import ir
from vcon_trajectories.sources.ir import (ACTION, HANDOFF, INCOMPLETE, MESSAGE,
                                          OBSERVATION, REASONING, TOOL_CALL,
                                          TOOL_RESULT, UTrajectory, _base_time)

VAC_SCHEMA_URL = "https://datatracker.ietf.org/doc/draft-birkholz-verifiable-agent-conversations/"
VAC_VERSION = "0.1.0"          # our record `version` (semver); not a spec value
EXTENSION_NAME = "agent_session"


def _entry_for(turn, model_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Map one IR Turn to a VAC `entry` (hyphenated keys, `type` discriminator)."""
    if turn.kind == MESSAGE:
        etype = "user" if turn.role == "user" else "assistant"
        e: Dict[str, Any] = {"type": etype, "content": turn.text}
        if etype == "assistant" and model_id:
            e["model-id"] = model_id
    elif turn.kind == REASONING:
        e = {"type": "reasoning", "content": turn.text}
    elif turn.kind in (TOOL_CALL, ACTION):
        e = {"type": "tool-call", "name": turn.tool_name, "input": turn.tool_input}
        if turn.meta.get("id"):
            e["call-id"] = turn.meta["id"]
    elif turn.kind == TOOL_RESULT:
        e = {"type": "tool-result", "output": turn.tool_result}
        if turn.meta.get("id"):
            e["call-id"] = turn.meta["id"]
        if turn.is_error:
            e["is-error"] = True
            e["status"] = "error"
    elif turn.kind == OBSERVATION:
        # environment observation -> tool-result (no call-id); labeled below
        e = {"type": "tool-result", "output": turn.text}
    elif turn.kind == HANDOFF:
        # VAC has no handoff type; use the extensible system-event (our choice)
        e = {"type": "system-event", "event-type": "agent-handoff",
             "data": {"from": turn.actor, "to": turn.handoff_to}}
    elif turn.kind == INCOMPLETE:
        e = {"type": "system-event", "event-type": "run-incomplete",
             "data": {"disposition": turn.disposition or "failed"}}
    else:
        return None
    if turn.timestamp:
        e["timestamp"] = turn.timestamp
    return e


def utrajectory_to_vac(
    ut: UTrajectory,
    *,
    model_id: str,
    model_provider: str,
    cli_name: Optional[str] = None,
    cli_version: Optional[str] = None,
    environment: Optional[Dict[str, Any]] = None,
    recording_agent: Optional[Dict[str, Any]] = None,
    version: str = VAC_VERSION,
) -> Dict[str, Any]:
    """Build a VAC `verifiable-agent-record` (unsigned) from an IR trajectory."""
    entries = [e for e in (_entry_for(t, model_id) for t in ut.turns) if e is not None]

    agent_meta: Dict[str, Any] = {"model-id": model_id, "model-provider": model_provider}
    if cli_name:
        agent_meta["cli-name"] = cli_name
    if cli_version:
        agent_meta["cli-version"] = cli_version

    session: Dict[str, Any] = {
        "session-id": ut.id or "session",
        "agent-meta": agent_meta,
        "entries": entries,
    }
    if environment:  # normalized {cwd, vcs_branch, vcs_commit, vcs_repo?}
        env: Dict[str, Any] = {"working-dir": environment.get("cwd", "")}
        vcs = {k: v for k, v in {
            "type": "git", "branch": environment.get("vcs_branch"),
            "revision": environment.get("vcs_commit"),
            "repository": environment.get("vcs_repo"),
        }.items() if v}
        if len(vcs) > 1:
            env["vcs"] = vcs
        session["environment"] = env
    stamps = [t.timestamp for t in ut.turns if t.timestamp]
    if stamps:
        session["session-start"] = stamps[0]
        session["session-end"] = stamps[-1]

    record: Dict[str, Any] = {
        "version": version,
        "id": f"{ut.source}#{ut.id}",
        "session": session,
    }
    base = _base_time(ut)
    record["created"] = _ts(base, 0)
    if recording_agent:
        record["recording-agent"] = recording_agent
    return record


def utrajectory_to_agent_session_vcon(
    ut: UTrajectory,
    *,
    model_id: str,
    provider: str,
    agent_name: Optional[str] = None,
    recording_agent: Optional[str] = None,
    environment: Optional[Dict[str, Any]] = None,
    critical: bool = False,
) -> Dict[str, Any]:
    """Build a core-shaped vCon carrying the `agent_session` extension.

    Per draft-howe: user prompts / assistant replies are ordinary `dialog[]` text
    entries; the full internal trace (tool calls/results/reasoning) is carried in
    ONE `analysis[]` entry of `type:"agent_trace"` whose body is the VAC record.
    """
    base = _base_time(ut)

    agent_session_meta: Dict[str, Any] = {"model_id": model_id, "provider": provider}
    if recording_agent:
        agent_session_meta["recording_agent"] = recording_agent
    if environment:
        agent_session_meta["environment"] = {
            k: v for k, v in {
                "cwd": environment.get("cwd"),
                "vcs_branch": environment.get("vcs_branch"),
                "vcs_commit": environment.get("vcs_commit"),
            }.items() if v
        }

    parties = [
        {"type": "person", "name": "user"},
        {"type": "bot", "name": agent_name or model_id, "role": "agent",
         "validation": "system", "meta": {"agent_session": agent_session_meta}},
    ]

    # dialog: only user/assistant messages (the trace lives in analysis)
    dialog: List[Dict[str, Any]] = []
    for turn in ut.turns:
        if turn.kind != MESSAGE:
            continue
        originator = 0 if turn.role == "user" else 1
        other = 1 if turn.role == "user" else 0
        dialog.append({
            "type": "text", "start": _ts(base, len(dialog)),
            "parties": [originator, other], "originator": originator,
            "mediatype": "text/plain", "body": turn.text or "", "encoding": "none",
        })

    vac = utrajectory_to_vac(
        ut, model_id=model_id, model_provider=provider,
        cli_name=recording_agent, environment=environment,
        recording_agent={"name": recording_agent} if recording_agent else None,
    )

    analysis = [{
        "type": "agent_trace",                       # draft-howe: MUST be this value
        "dialog": list(range(len(dialog))),
        "vendor": provider,
        "product": model_id,
        "schema": VAC_SCHEMA_URL,
        "mediatype": "application/json",
        "body": vac,                                 # the VAC verifiable-agent-record
        "encoding": "json",
    }]

    vcon: Dict[str, Any] = {
        "vcon": "0.4.0",
        "uuid": deterministic_uuid8(f"agent_session:{ut.source}#{ut.id}"),
        "created_at": _ts(base, 0),
        "subject": ut.subject or ut.id,
        "extensions": [EXTENSION_NAME],
        "parties": parties,
        "dialog": dialog,
        "analysis": analysis,
    }
    if critical:
        vcon["critical"] = [EXTENSION_NAME]
    return vcon
