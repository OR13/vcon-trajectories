"""Normalized intermediate representation of an agent trajectory.

Both eval formats (single-turn generations and multi-round tool use) are parsed
into these dataclasses so the vCon converter can treat them uniformly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class ToolCall:
    """A single tool invocation and its result within a round.

    The source eval logs occasionally truncate the tool argument / result JSON,
    so the raw strings are always preserved and the parsed values are best-effort
    (``None`` when the JSON could not be parsed).
    """

    name: str
    input: Optional[Any]      # parsed args, or None if unparseable/truncated
    input_raw: str
    result: Optional[Any]     # parsed result, or None if unparseable/truncated
    result_raw: str


@dataclass
class Round:
    """One turn of the model: its reasoning plus at most one tool call.

    A round with no tool call is a terminal / answer-producing turn.
    """

    index: int
    reasoning: str = ""
    tool_call: Optional[ToolCall] = None


@dataclass
class Trajectory:
    """A single agent trajectory (one prompt / test case) → one vCon."""

    source_repo: str
    source_file: str
    test_id: str                       # e.g. "math_compute" or "sample-01"
    kind: str                          # "tool_test" | "sample_generation"
    model: str
    prompt: str
    rounds: List[Round] = field(default_factory=list)
    final_answer: str = ""
    category: Optional[str] = None     # sample_generations only
    duration_s: Optional[float] = None  # tool_test only
    n_rounds: Optional[int] = None      # tool_test only (as declared in header)

    @property
    def tools_used(self) -> List[str]:
        seen: List[str] = []
        for r in self.rounds:
            if r.tool_call and r.tool_call.name not in seen:
                seen.append(r.tool_call.name)
        return seen

    @property
    def subject(self) -> str:
        if self.kind == "sample_generation":
            excerpt = " ".join(self.prompt.split())[:80]
            cat = f"[{self.category}] " if self.category else ""
            return f"{cat}{excerpt}"
        return self.test_id
