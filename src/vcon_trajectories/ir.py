"""Vendor-neutral intermediate representation of an agent trajectory.

Every vendor-native format (Claude Code JSONL, Codex rollout JSONL, Gemini CLI
turns, ...) and every benchmark corpus is parsed into a `UTrajectory`: metadata
plus an ordered list of `Turn`s. `ai_agent.utrajectory_to_vcon` is the single
place that maps this IR onto the vCon `ai_agent` extension.

The Turn kinds deliberately mirror the entry kinds of the draft
(message / tool-call / tool-result / reasoning / system-event) plus a few kinds
the draft has no first-class construct for (GUI ACTION/OBSERVATION, HANDOFF,
INCOMPLETE); `docs/draft-feedback.md` tracks how each is represented.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

MESSAGE = "message"
TOOL_CALL = "tool_call"
TOOL_RESULT = "tool_result"
REASONING = "reasoning"
SYSTEM = "system"            # lifecycle / bookkeeping entry (event_type + data)
# No first-class draft construct; represented via system-event (see docs/draft-feedback.md).
ACTION = "action"            # GUI/environment action taken by the agent
OBSERVATION = "observation"  # environment state returned to the agent
HANDOFF = "handoff"          # agent -> agent delegation (peer, not a spawned child)
INCOMPLETE = "incomplete"    # aborted / failed run

MAIN = "main"                # key of the root agent session


@dataclass
class Turn:
    kind: str
    actor: str = "assistant"         # party label: "user", "assistant", or an agent name
    role: str = "assistant"          # user | assistant | system | tool | agent | environment
    text: Optional[str] = None       # message / reasoning / observation content
    tool_name: Optional[str] = None
    tool_input: Any = None
    tool_result: Any = None
    is_error: Optional[bool] = None
    status: Optional[str] = None
    timestamp: Optional[str] = None  # RFC 3339, if the source carries one
    # Native trace structure
    call_id: Optional[str] = None
    entry_id: Optional[str] = None
    parent_id: Optional[str] = None
    session: str = MAIN              # which agent session this entry belongs to
    # Model attribution (assistant messages)
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None   # input/output/cached/reasoning/total/cost
    # Reasoning
    encrypted: Optional[str] = None
    subject: Optional[str] = None
    # SYSTEM
    event_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    # HANDOFF / INCOMPLETE
    handoff_to: Optional[str] = None
    disposition: Optional[str] = None
    mediatype: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChildSession:
    parent: str = MAIN
    description: Optional[str] = None
    agent_session_id: Optional[str] = None


@dataclass
class UTrajectory:
    source: str                      # corpus id (attribution + uuid namespace)
    id: str
    subject: str = ""
    turns: List[Turn] = field(default_factory=list)
    created_at: Optional[datetime] = None
    # Agent identity -> Party.agent_meta
    agent_meta: Optional[Dict[str, Any]] = None
    # Execution context -> Session.environment, vCon.vcs
    environment: Optional[Dict[str, Any]] = None
    vcs: Optional[Dict[str, Any]] = None
    agent_session_id: Optional[str] = None
    format: Optional[str] = None     # "interactive" / "autonomous"
    child_sessions: Dict[str, ChildSession] = field(default_factory=dict)
    # Not mapped to draft constructs; carried as an attachment so nothing is lost.
    system: Optional[str] = None
    tools: Any = None
    outcome: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
