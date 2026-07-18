"""Parsers for the Qwythos eval markdown logs → :class:`Trajectory` objects.

Two formats are handled:

* ``tool_test_outputs.md`` — multi-round agentic tool use.
* ``sample_generations.md`` — single-turn reasoning + answer.

The source logs are human-formatted and occasionally truncate embedded JSON, so
the parsers are deliberately tolerant: raw strings are always kept and JSON is
parsed best-effort.
"""
from __future__ import annotations

import json
import re
from typing import Any, Iterator, List, Optional, Tuple

from .models import Round, ToolCall, Trajectory

DEFAULT_MODEL = "Qwythos-9B-Claude-Mythos-5-1M"

_TOOL_TEST_HEADER = re.compile(
    r"^## (?P<name>.+?) \((?P<rounds>\d+) rounds · (?P<dur>[\d.]+)s\)\s*$",
    re.MULTILINE,
)
_SAMPLE_HEADER = re.compile(
    r"^## (?P<num>\d+)\. \[(?P<cat>[a-z-]+)\]\s*$",
    re.MULTILINE,
)
_ROUND_HEADER = re.compile(
    r"^### Round (?P<idx>\d+) · tool_calls=(?P<n>\d+)\s*$",
    re.MULTILINE,
)


def _try_json(s: str) -> Optional[Any]:
    try:
        return json.loads(s)
    except Exception:
        return None


def _blocks(text: str, header: re.Pattern) -> Iterator[Tuple[re.Match, str]]:
    """Yield (header_match, body_text) for each top-level header in ``text``.

    Body runs from the end of the header line to the start of the next header
    (or end of file), so header-like lines inside a body are not confused for
    new entries.
    """
    matches = list(header.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        yield m, text[start:end]


def _first(pattern: str, text: str, flags: int = re.MULTILINE) -> Optional[str]:
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


def _parse_reasoning(chunk: str) -> str:
    """Extract the model's thinking (fenced text up to ``</think>``)."""
    m = re.search(r"```\s*\n(.*?)</think>", chunk, re.DOTALL)
    return m.group(1).strip() if m else ""


def _parse_tool_call(chunk: str) -> Optional[ToolCall]:
    call_line = _first(r"^\*\*Tool call:\*\* `(.+)`\s*$", chunk)
    if call_line is None:
        return None
    m = re.match(r"([A-Za-z_]\w*)\((.*)$", call_line)
    if not m:
        return None
    name, rest = m.group(1), m.group(2)
    # Normal form ends with ")"; truncated logs may not — try both.
    candidate = rest[:-1] if rest.endswith(")") else rest
    parsed = _try_json(candidate)
    if parsed is not None:
        input_raw, input_val = candidate, parsed
    else:
        input_raw, input_val = rest, _try_json(rest)

    result_raw = _first(r"^\*\*Result:\*\* `(.*)`\s*$", chunk) or ""
    return ToolCall(
        name=name,
        input=input_val,
        input_raw=input_raw,
        result=_try_json(result_raw),
        result_raw=result_raw,
    )


def _clean_final_answer(section: str) -> str:
    """The final-answer block repeats the last round's thinking; keep the
    visible answer after the last ``</think>``."""
    section = section.strip()
    if "</think>" in section:
        section = section.rsplit("</think>", 1)[1]
    return section.strip().strip("-").strip()


def parse_tool_tests(
    text: str, source_repo: str, source_file: str, model: str = DEFAULT_MODEL
) -> List[Trajectory]:
    trajectories: List[Trajectory] = []
    for header, body in _blocks(text, _TOOL_TEST_HEADER):
        name = header.group("name").strip()
        prompt = _first(r"^\*\*Prompt:\*\* (.+?)\s*$", body) or ""

        # Split body into round chunks, then a trailing final-answer section.
        round_headers = list(_ROUND_HEADER.finditer(body))
        final_match = re.search(r"^\*\*Final answer:\*\*\s*$", body, re.MULTILINE)
        final_start = final_match.start() if final_match else len(body)

        rounds: List[Round] = []
        for i, rh in enumerate(round_headers):
            chunk_start = rh.end()
            chunk_end = (
                round_headers[i + 1].start()
                if i + 1 < len(round_headers)
                else final_start
            )
            chunk = body[chunk_start:chunk_end]
            rounds.append(
                Round(
                    index=int(rh.group("idx")),
                    reasoning=_parse_reasoning(chunk),
                    tool_call=_parse_tool_call(chunk),
                )
            )

        final_answer = (
            _clean_final_answer(body[final_match.end():]) if final_match else ""
        )
        trajectories.append(
            Trajectory(
                source_repo=source_repo,
                source_file=source_file,
                test_id=name,
                kind="tool_test",
                model=model,
                prompt=prompt,
                rounds=rounds,
                final_answer=final_answer,
                duration_s=float(header.group("dur")),
                n_rounds=int(header.group("rounds")),
            )
        )
    return trajectories


def parse_sample_generations(
    text: str, source_repo: str, source_file: str, model: str = DEFAULT_MODEL
) -> List[Trajectory]:
    trajectories: List[Trajectory] = []
    for header, body in _blocks(text, _SAMPLE_HEADER):
        num = header.group("num")
        cat = header.group("cat")
        prompt = _first(r"^\*\*Prompt:\*\* (.+?)\s*$", body) or ""

        reasoning = ""
        rm = re.search(
            r"\*\*🧠 Reasoning\*\*[^\n]*:\s*\n(.*?)\n\*\*✅ Answer:\*\*",
            body,
            re.DOTALL,
        )
        if rm:
            reasoning = rm.group(1).strip()

        answer = ""
        am = re.search(r"\*\*✅ Answer:\*\*\s*\n(.*)$", body, re.DOTALL)
        if am:
            answer = am.group(1).strip().strip("-").strip()

        trajectories.append(
            Trajectory(
                source_repo=source_repo,
                source_file=source_file,
                test_id=f"sample-{int(num):02d}",
                kind="sample_generation",
                model=model,
                prompt=prompt,
                rounds=[Round(index=0, reasoning=reasoning, tool_call=None)],
                final_answer=answer,
                category=cat,
            )
        )
    return trajectories
