"""End-to-end pipeline: parse Qwythos eval logs → vCon 0.4.0 → validate → write.

    python -m vcon_trajectories [--data-dir data/qwythos_evals] [--out-dir out]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List

from .convert import trajectory_to_vcon
from .models import Trajectory
from .parse import parse_sample_generations, parse_tool_tests
from .validate import make_validator, pyvcon_available, pyvcon_roundtrip, validate_vcon

_REPO = "empero-ai/Qwythos-9B-Claude-Mythos-5-1M"


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_trajectories(data_dir: str) -> List[Trajectory]:
    trajectories: List[Trajectory] = []
    tool_file = os.path.join(data_dir, "tool_test_outputs.md")
    sample_file = os.path.join(data_dir, "sample_generations.md")
    if os.path.exists(tool_file):
        trajectories += parse_tool_tests(_read(tool_file), _REPO, "evals/tool_test_outputs.md")
    if os.path.exists(sample_file):
        trajectories += parse_sample_generations(_read(sample_file), _REPO, "evals/sample_generations.md")
    return trajectories


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert Mythos trajectories to validated vCons.")
    parser.add_argument("--data-dir", default="data/qwythos_evals")
    parser.add_argument("--out-dir", default="out")
    parser.add_argument("--schema", default=None, help="Path to vCon JSON schema.")
    parser.add_argument("--no-pyvcon", action="store_true", help="Skip the python-vcon cross-check.")
    args = parser.parse_args(argv)

    trajectories = load_trajectories(args.data_dir)
    if not trajectories:
        print(f"No eval logs found under {args.data_dir!r}. See docs/data-source.md.", file=sys.stderr)
        return 2

    os.makedirs(args.out_dir, exist_ok=True)
    schema = None
    if args.schema:
        from .validate import load_schema

        schema = load_schema(args.schema)
    validator = make_validator(schema)

    n_ok = 0
    n_fail = 0
    total_dialogs = 0
    print(f"Converting {len(trajectories)} trajectories from {_REPO}\n")
    for traj in trajectories:
        vcon = trajectory_to_vcon(traj)
        errors = validate_vcon(vcon, validator)
        total_dialogs += len(vcon["dialog"])
        out_path = os.path.join(args.out_dir, f"{traj.test_id}.vcon.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(vcon, f, indent=2, ensure_ascii=False)

        status = "VALID  " if not errors else "INVALID"
        tools = f" tools={','.join(traj.tools_used)}" if traj.tools_used else ""
        print(f"  [{status}] {traj.test_id:<22} dialogs={len(vcon['dialog']):<2} "
              f"analysis={len(vcon['analysis'])}{tools}")
        if errors:
            n_fail += 1
            for e in errors[:8]:
                print(f"            - {e}")
        else:
            n_ok += 1

    print(f"\nResult: {n_ok}/{len(trajectories)} valid against vCon JSON Schema "
          f"(v0.4.0), {total_dialogs} total dialog entries.")
    print(f"vCons written to {args.out_dir}/")

    if not args.no_pyvcon and pyvcon_available():
        sample = trajectory_to_vcon(trajectories[0])
        print(f"\npython-vcon reference cross-check: {pyvcon_roundtrip(sample)}")
    elif not args.no_pyvcon:
        print("\npython-vcon reference cross-check: skipped (package not installed).")

    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
