#!/usr/bin/env python3
"""Validate against the pinned draft CDDL.

1. Controls: the draft's own positive examples must pass, its negative examples fail.
2. Every generated vCon under examples/ must pass CDDL + the semantic checks.

    python scripts/validate.py
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "src"))
from vcon_trajectories.validate import CddlValidator, semantic_issues  # noqa: E402


def main() -> int:
    v = CddlValidator()
    bad = 0
    print("== draft controls ==")
    for f in sorted(glob.glob(f"{HERE}/schema/ai-agent/examples/*.json")):
        ok, msg = v.validate_path(f)
        bad += not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] positive {os.path.basename(f)} {msg}")
    for f in sorted(glob.glob(f"{HERE}/schema/ai-agent/negative/*.json")):
        ok, _ = v.validate_path(f)
        bad += ok
        print(f"  [{'PASS' if not ok else 'FAIL'}] negative {os.path.basename(f)} (rejected={not ok})")
    print("== generated vCons ==")
    files = sorted(glob.glob(f"{HERE}/examples/**/*.vcon.json", recursive=True))
    n_ok = 0
    for f in files:
        ok, msg = v.validate_path(f)
        issues = semantic_issues(json.load(open(f)))
        good = ok and not issues
        n_ok += good
        print(f"  [{'PASS' if good else 'FAIL'}] {os.path.relpath(f, HERE)} {msg} {issues[:3] or ''}")
    print(f"\n{n_ok}/{len(files)} generated vCons valid (CDDL + semantic); controls failures: {bad}")
    return 0 if (n_ok == len(files) and not bad) else 1


if __name__ == "__main__":
    raise SystemExit(main())
