"""Tests for the EXPERIMENTAL agent_session/VAC prototype (run separately from
the core suite):

    PYTHONPATH=src pytest experiments/vac-agent-session/test_vac.py

Validates the committed example vCons against the core vCon JSON Schema and checks
the agent_session + VAC structure. If the Ruby `cddl` gem is available, the VAC
records are also validated against the vendored VAC CDDL.
"""
import glob
import json
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "src"))

from vcon_trajectories.validate import make_validator, validate_vcon  # noqa: E402

VCONS = sorted(glob.glob(os.path.join(HERE, "examples", "*.vcon.json")))
VACS = sorted(glob.glob(os.path.join(HERE, "examples", "*.vac.json")))
CDDL = os.path.join(HERE, "agent-conversation.cddl")


@pytest.fixture(scope="module")
def validator():
    return make_validator()


def test_outer_vcons_valid_core_and_shaped(validator):
    assert VCONS, "no example vCons; run build_examples.py"
    for path in VCONS:
        vcon = json.load(open(path))
        assert validate_vcon(vcon, validator) == [], f"{os.path.basename(path)} invalid core vCon"
        assert vcon["extensions"] == ["agent_session"]
        agent = [p for p in vcon["parties"] if p.get("role") == "agent"]
        assert agent and "agent_session" in agent[0]["meta"]
        assert agent[0]["meta"]["agent_session"]["model_id"]
        assert agent[0]["meta"]["agent_session"]["provider"]
        traces = [a for a in vcon["analysis"] if a["type"] == "agent_trace"]
        assert len(traces) == 1
        rec = traces[0]["body"]
        assert rec["version"] and rec["id"] and rec["session"]["entries"]
        assert rec["session"]["agent-meta"]["model-id"]        # hyphenated in VAC


def test_vac_records_have_typed_entries():
    for path in VACS:
        rec = json.load(open(path))
        types = {e["type"] for e in rec["session"]["entries"]}
        assert types  # non-empty
        assert types <= {"user", "assistant", "tool-call", "tool-result",
                         "reasoning", "system-event"}


@pytest.mark.skipif(not shutil.which("ruby"), reason="ruby/cddl gem not available")
def test_vac_records_validate_against_vac_cddl():
    try:
        bindir = subprocess.check_output(["ruby", "-e", "print Gem.bindir"], text=True).strip()
    except Exception:
        pytest.skip("cannot resolve Gem.bindir")
    cddl_bin = os.path.join(bindir, "cddl")
    if not os.path.exists(cddl_bin):
        pytest.skip("cddl gem not installed")
    assert VACS
    for path in VACS:
        proc = subprocess.run([cddl_bin, CDDL, "validate", path], capture_output=True, text=True)
        assert proc.returncode == 0, f"{os.path.basename(path)} failed VAC CDDL: {proc.stdout[:300]}"
