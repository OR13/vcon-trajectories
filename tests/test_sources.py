"""Tests for the multi-source adapters + IR converter.

Adapter unit tests use tiny inline records (no network). The committed example
vCons under examples/sources/ are validated against the schema offline.

Run with: PYTHONPATH=src pytest
"""
import glob
import json
import os

import pytest

from vcon_trajectories.sources import adapters as A
from vcon_trajectories.sources.ir import utrajectory_to_vcon
from vcon_trajectories.validate import make_validator, validate_vcon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES = sorted(glob.glob(os.path.join(ROOT, "examples", "sources", "*.vcon.json")))


@pytest.fixture(scope="module")
def validator():
    return make_validator()


def _tool_call_dialogs(vcon):
    return [d for d in vcon["dialog"]
            if d.get("encoding") == "json" and isinstance(d.get("body"), dict) and "tool" in d["body"]]


def test_all_committed_examples_are_schema_valid(validator):
    assert EXAMPLES, "no example vCons found"
    for path in EXAMPLES:
        vcon = json.load(open(path, encoding="utf-8"))
        assert validate_vcon(vcon, validator) == [], f"{os.path.basename(path)}: invalid"
        assert vcon["vcon"] == "0.4.0"


def test_hermes_parallel_tool_calls():
    rec = {
        "id": "x",
        "conversations": [
            {"from": "human", "value": "check both cameras"},
            {"from": "gpt", "value": "On it.\n<tool_call>\n{\"name\": \"cam\", \"arguments\": {\"id\": \"a\"}}\n</tool_call>\n<tool_call>\n{\"name\": \"cam\", \"arguments\": {\"id\": \"b\"}}\n</tool_call>"},
        ],
        "tools": "[]",
    }
    vcon = utrajectory_to_vcon(A.hermes(rec))
    calls = _tool_call_dialogs(vcon)
    assert len(calls) == 2  # two tool calls emitted from one assistant turn
    assert {c["body"]["input"]["id"] for c in calls} == {"a", "b"}


def test_api_bank_tool_error_flag():
    turns = [
        {"role": "User", "text": "log in"},
        {"role": "API", "api_name": "GetToken", "param_dict": {"u": "x"},
         "result": {"exception": "invalid credentials"}},
    ]
    vcon = utrajectory_to_vcon(A.api_bank(turns, "t1"))
    errs = [d for d in vcon["dialog"] if isinstance(d.get("body"), dict) and d["body"].get("is_error")]
    assert len(errs) == 1


def test_openai_think_becomes_reasoning_analysis():
    rec = {"task_id": 1, "trial": 0, "reward": 1.0, "traj": [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": None,
         "tool_calls": [{"id": "c1", "type": "function",
                         "function": {"name": "think", "arguments": "{\"thought\": \"I should greet.\"}"}}]},
        {"role": "assistant", "content": "Hello!"},
    ]}
    vcon = utrajectory_to_vcon(A.tau_bench(rec))
    cot = [a for a in vcon["analysis"] if a["schema"] == "chain-of-thought"]
    assert len(cot) == 1 and "greet" in cot[0]["body"]
    # reward carried into the metadata report
    rep = [a for a in vcon["analysis"] if a["schema"] == "trajectory-metadata"][0]
    assert rep["body"]["reward"] == 1.0


def test_agent_traces_preserves_real_timestamps():
    rec = {
        "session_id": "s", "prompt": "do x", "sent_at": "2026-06-12T00:40:34.865Z",
        "tools": [], "messages": [],
        "trace": [
            {"type": "user", "timestamp": "2026-06-12T00:40:34.865Z",
             "message": {"role": "user", "content": "do x"}},
            {"type": "assistant", "timestamp": "2026-06-12T00:41:10.100Z",
             "message": {"role": "assistant", "content": [
                 {"type": "tool_use", "id": "t1", "name": "bash", "input": {"cmd": "ls"}}]}},
            {"type": "user", "timestamp": "2026-06-12T00:41:12.500Z",
             "message": {"role": "user", "content": [
                 {"type": "tool_result", "tool_use_id": "t1", "content": "nope", "is_error": True}]}},
        ],
    }
    vcon = utrajectory_to_vcon(A.agent_traces(rec))
    starts = [d["start"] for d in vcon["dialog"]]
    assert "2026-06-12T00:41:10.100000Z" in starts  # real source timestamp, not synthesized
    errs = [d for d in vcon["dialog"] if isinstance(d.get("body"), dict) and d["body"].get("is_error")]
    assert len(errs) == 1  # real tool error captured


def test_mind2web_actions_and_observations():
    rec = {"annotation_id": "a", "confirmed_task": "book a table", "website": "w",
           "domain": "d", "subdomain": "s",
           "action_reprs": ["CLICK [button] Search"],
           "actions": [{"action_uid": "u1", "cleaned_html": "<html>...</html>",
                        "operation": {"op": "CLICK", "value": ""}, "pos_candidates": []}]}
    vcon = utrajectory_to_vcon(A.mind2web(rec))
    # user goal + observation + action
    assert vcon["dialog"][0]["originator"] == 0  # user goal
    kinds = [d.get("application") for d in vcon["dialog"]]
    assert "CLICK" in kinds
