"""Exporters (ATIF, OTel GenAI) and the ATIF importer, on the committed examples plus a
synthetic sidechain vCon. The ATIF/OTel checks are re-implementations of the specs' rules
(see export/*_check.py), so these tests pin behaviour; they are not conformance certificates."""
import glob
import json
import os

import pytest

from vcon_trajectories.ai_agent import utrajectory_to_vcon
from vcon_trajectories.export.atif import to_atif
from vcon_trajectories.export.atif_check import check_atif
from vcon_trajectories.export.otel_check import check_otel
from vcon_trajectories.export.otel_genai import to_otel
from vcon_trajectories.native import atif as atif_native
from vcon_trajectories.native import claude_code

from test_native import _cc

EXAMPLES = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "examples", "*", "*.vcon.json")))


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: os.path.basename(p))
def test_examples_export_clean(path):
    v = json.load(open(path, encoding="utf-8"))
    assert check_atif(to_atif(v)) == []
    assert check_otel(to_otel(v)) == []


def test_sidechain_becomes_embedded_subagent_and_child_invoke_agent():
    v = utrajectory_to_vcon(claude_code.parse(_cc()))
    a = to_atif(v)
    assert check_atif(a) == []
    assert len(a["subagent_trajectories"]) == 1
    refs = [r for s in a["steps"] for r in (s.get("observation") or {}).get("results", [])
            if r.get("subagent_trajectory_ref")]
    assert len(refs) == 1  # attached to the Task call's result, not a fallback system step
    spans = to_otel(v)
    assert check_otel(spans) == []
    invoke = [s for s in spans if s["name"].startswith("invoke_agent")]
    assert len(invoke) == 2
    child = next(s for s in invoke if s["parent_span_id"])
    parent = next(s for s in spans if s["span_id"] == child["parent_span_id"])
    assert parent["name"] == "execute_tool Task"


def test_claude_input_tokens_are_inclusive_of_cache():
    v = utrajectory_to_vcon(claude_code.parse(_cc()))
    tc = next(e for e in v["events"] if e.get("event_type") == "token-count")
    # fixture: input_tokens 5 (excl. cache), cache_read 3 -> inclusive input is 8
    assert tc["data"]["input"] == 8 and tc["data"]["cached"] == 3
    a = to_atif(v)
    m = next(s["metrics"] for s in a["steps"] if s.get("metrics"))
    assert m["cached_tokens"] <= m["prompt_tokens"]


def test_roundtrip_preserves_tool_pairing_and_errors():
    v = utrajectory_to_vcon(claude_code.parse(_cc()))
    back = utrajectory_to_vcon(atif_native.parse_trajectory(to_atif(v), id="rt", source="rt"))
    flag = lambda x: sorted((e["call_id"], e.get("is_error")) for e in x["events"] if e["type"] == "tool-result")
    assert flag(back) == flag(v)


def test_atif_check_rejects_bad_trajectories():
    v = json.load(open(EXAMPLES[0], encoding="utf-8"))
    a = to_atif(v)
    a["steps"][1]["step_id"] = 99
    assert any("sequential" in e for e in check_atif(a))
    a = to_atif(v)
    step = next(s for s in a["steps"] if s.get("observation"))
    step["observation"]["results"][0]["source_call_id"] = "nope"
    assert any("matches no tool_call" in e for e in check_atif(a))
