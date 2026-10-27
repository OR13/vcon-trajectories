"""Checks for the span list from `to_otel`, written from the OTel GenAI conventions text.

Not the reference pydantic models (`schema/otel-genai/models.py`, which this repo vendors but
does not execute): it re-states the constraints that matter for trajectories. Covered:
span-tree integrity, `gen_ai.operation.name` vs span name, Required attributes, the
"input_tokens INCLUDES cached tokens" rule, and the shape of `gen_ai.output.messages` parts
(text / reasoning need `content`; tool_call needs `name`; unknown part types need a `type`).
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

_OPS = {"invoke_agent", "chat", "execute_tool"}
_PART_REQUIRED = {"text": ("content",), "reasoning": ("content",), "tool_call": ("name",),
                  "tool_call_response": ("response",)}


def check_otel(spans: List[Dict[str, Any]]) -> List[str]:
    errs: List[str] = []
    ids = {s["span_id"] for s in spans}
    if len(ids) != len(spans):
        errs.append("duplicate span_id")
    if len({s["trace_id"] for s in spans}) != 1:
        errs.append("spans must share one trace_id")
    roots = [s for s in spans if s["parent_span_id"] is None]
    if len(roots) != 1:
        errs.append(f"expected exactly one root span, found {len(roots)}")
    for s in spans:
        a, n = s["attributes"], s["name"]
        p = f"span {n!r}"
        if s["parent_span_id"] is not None and s["parent_span_id"] not in ids:
            errs.append(f"{p}: parent_span_id not in trace")
        if s["end_time_unix_nano"] < s["start_time_unix_nano"]:
            errs.append(f"{p}: ends before it starts")
        op = a.get("gen_ai.operation.name")
        if op not in _OPS:
            errs.append(f"{p}: gen_ai.operation.name {op!r} unexpected")
            continue
        if not n.startswith(op):
            errs.append(f"{p}: span name SHOULD start with the operation name {op!r}")
        if op == "execute_tool":
            if not a.get("gen_ai.tool.name") or not a.get("gen_ai.tool.call.id"):
                errs.append(f"{p}: gen_ai.tool.name and gen_ai.tool.call.id expected")
            if s["status"]["code"] == "ERROR" and not a.get("error.type"):
                errs.append(f"{p}: error.type is Required when the operation failed")
        if op == "chat" and not a.get("gen_ai.provider.name"):
            errs.append(f"{p}: gen_ai.provider.name is Required on chat spans")
        inp, cr, cw = (a.get("gen_ai.usage.input_tokens"), a.get("gen_ai.usage.cache_read.input_tokens"),
                       a.get("gen_ai.usage.cache_write.input_tokens"))
        if inp is not None and (cr or 0) + (cw or 0) > inp:
            errs.append(f"{p}: cache tokens exceed input_tokens (input_tokens INCLUDES cached tokens)")
        om = a.get("gen_ai.output.messages")
        if om is not None:
            try:
                msgs = json.loads(om)
            except ValueError:
                errs.append(f"{p}: gen_ai.output.messages is not JSON")
                continue
            for m in msgs:
                if "role" not in m or not isinstance(m.get("parts"), list):
                    errs.append(f"{p}: message needs role and parts[]")
                    continue
                for part in m["parts"]:
                    t = part.get("type")
                    if not isinstance(t, str):
                        errs.append(f"{p}: part without type")
                    for req in _PART_REQUIRED.get(t, ()):
                        if req not in part:
                            errs.append(f"{p}: {t} part missing {req!r}")
    return errs
