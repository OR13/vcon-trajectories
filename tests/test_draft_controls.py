import glob
import json
import os

import pytest

from vcon_trajectories.validate import CddlValidator, HERE, semantic_issues


@pytest.fixture(scope="module")
def v():
    try:
        return CddlValidator()
    except Exception:
        pytest.skip("ruby cddl gem not available")


def test_draft_positive_examples(v):
    for f in glob.glob(f"{HERE}/schema/ai-agent/examples/*.json"):
        assert v.validate_path(f)[0], f


def test_draft_negative_examples_rejected(v):
    fs = glob.glob(f"{HERE}/schema/ai-agent/negative/*.json")
    assert len(fs) == 12
    for f in fs:
        assert not v.validate_path(f)[0], f


def test_committed_examples_valid(v):
    fs = glob.glob(f"{HERE}/examples/**/*.vcon.json", recursive=True)
    assert len(fs) >= 10
    for f in fs:
        assert v.validate_path(f)[0], f
        assert semantic_issues(json.load(open(f))) == [], f
