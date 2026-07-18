"""Tests for the trajectory -> vCon pipeline.

Run with: PYTHONPATH=src pytest
"""
import json
import os

import pytest

from vcon_trajectories.convert import deterministic_uuid8, trajectory_to_vcon
from vcon_trajectories.parse import parse_sample_generations, parse_tool_tests
from vcon_trajectories.validate import make_validator, validate_vcon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "qwythos_evals")
REPO = "empero-ai/Qwythos-9B-Claude-Mythos-5-1M"


def _read(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def validator():
    return make_validator()


@pytest.fixture(scope="module")
def tool_trajectories():
    return parse_tool_tests(_read("tool_test_outputs.md"), REPO, "evals/tool_test_outputs.md")


@pytest.fixture(scope="module")
def sample_trajectories():
    return parse_sample_generations(_read("sample_generations.md"), REPO, "evals/sample_generations.md")


def test_parse_counts(tool_trajectories, sample_trajectories):
    assert len(tool_trajectories) == 7
    assert len(sample_trajectories) == 25


def test_tool_test_structure(tool_trajectories):
    t = {x.test_id: x for x in tool_trajectories}["math_compute"]
    assert t.kind == "tool_test"
    assert t.tools_used == ["python_executor"]
    assert t.prompt.startswith("Compute sin(pi/7)")
    assert t.final_answer  # non-empty
    # first round has a tool call with real parsed args
    assert t.rounds[0].tool_call is not None
    assert "code" in t.rounds[0].tool_call.input


def test_sample_structure(sample_trajectories):
    t = sample_trajectories[0]
    assert t.kind == "sample_generation"
    assert t.category == "cyber"
    assert t.rounds[0].reasoning
    assert t.final_answer
    assert t.tools_used == []


def test_all_convert_and_validate(tool_trajectories, sample_trajectories, validator):
    for traj in tool_trajectories + sample_trajectories:
        vcon = trajectory_to_vcon(traj)
        errors = validate_vcon(vcon, validator)
        assert errors == [], f"{traj.test_id}: {errors}"
        assert vcon["vcon"] == "0.4.0"
        assert vcon["dialog"][0]["originator"] == 0  # user speaks first


def test_tool_dialog_wiring(tool_trajectories, validator):
    t = {x.test_id: x for x in tool_trajectories}["math_compute"]
    vcon = trajectory_to_vcon(t)
    # user -> agent(tool_call) -> tool(result) -> agent(answer)
    originators = [d["originator"] for d in vcon["dialog"]]
    assert originators == [0, 1, 2, 1]
    # tool party (index 2) is the python_executor bot
    assert vcon["parties"][2]["name"] == "python_executor"
    # tool call and result are JSON-encoded
    assert vcon["dialog"][1]["encoding"] == "json"
    assert vcon["dialog"][2]["body"]["stdout"].startswith("0.4163")
    # reasoning captured as chain-of-thought analysis linked to the call dialog
    cot = [a for a in vcon["analysis"] if a["schema"] == "chain-of-thought"]
    assert any(a["dialog"] == [1] for a in cot)


def test_truncated_json_is_tolerated(tool_trajectories):
    # primes_simulation's tool-call arguments are truncated in the source log.
    t = {x.test_id: x for x in tool_trajectories}["primes_simulation"]
    vcon = trajectory_to_vcon(t)
    call_body = vcon["dialog"][1]["body"]
    # unparseable args are preserved raw rather than dropped
    assert "_raw_arguments" in call_body["input"]
    # ...but the (valid) result JSON is parsed normally
    assert vcon["dialog"][2]["body"]["stdout"].strip() == "9592"


def test_deterministic_uuid_is_v8_and_stable():
    u1 = deterministic_uuid8("a")
    u2 = deterministic_uuid8("a")
    assert u1 == u2
    assert deterministic_uuid8("a") != deterministic_uuid8("b")
    assert u1[14] == "8"  # version nibble


def test_mythos_sample_is_valid_and_compatible(validator):
    """The publishable synthetic sample uses the gated dataset's schema and the
    same converter, so it must validate and carry the same vCon structure."""
    from vcon_trajectories.mythos import record_to_vcon

    with open(os.path.join(ROOT, "examples", "mythos_agent_sample_record.json"), encoding="utf-8") as f:
        record = json.load(f)
    vcon = record_to_vcon(record)
    assert validate_vcon(vcon, validator) == []
    assert vcon["vcon"] == "0.4.0"
    # created_at is taken from the record (not synthesized)
    assert vcon["created_at"] == "2026-07-18T00:00:00Z"
    # tool trajectory: user -> assistant text -> tool_use -> tool_result -> answer
    assert [d["originator"] for d in vcon["dialog"]] == [0, 1, 1, 2, 1]
    assert vcon["parties"][2]["name"] == "web_search"
    purposes = {a["purpose"] for a in vcon["attachments"]}
    assert purposes == {"system-prompt", "tool-definitions"}
    # the committed sample .vcon.json is up to date with the converter
    with open(os.path.join(ROOT, "examples", "mythos_agent_sample.vcon.json"), encoding="utf-8") as f:
        assert json.load(f) == vcon


def test_negative_validation(validator):
    bad = {"vcon": "0.4.0", "uuid": "nope", "created_at": "someday",
           "dialog": [{"type": "chat", "start": "x"}]}
    errors = validate_vcon(bad, validator)
    joined = " ".join(errors)
    assert "uuid" in joined and "date-time" in joined and "chat" in joined
