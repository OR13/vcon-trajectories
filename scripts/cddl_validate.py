#!/usr/bin/env python3
"""Validate vCon JSON files against schema/vcon.cddl using the Ruby `cddl` gem.

The `cddl` gem (Bormann's RFC 8610 reference implementation, v0.12.x) is the tool
this CDDL was written for. Because the gem's `cddl` binary is often shadowed on
PATH by the Rust `cddl` crate, this script resolves the gem binary via
`Gem.bindir`.

    python scripts/cddl_validate.py out/*.vcon.json examples/*.vcon.json

Exit code is non-zero if any file fails. Pass --json <path> to also dump a
machine-readable result summary.
"""
import argparse
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CDDL = os.path.join(HERE, "schema", "vcon.cddl")


def gem_cddl_bin() -> str:
    try:
        bindir = subprocess.check_output(
            ["ruby", "-e", "print Gem.bindir"], text=True
        ).strip()
    except Exception as exc:
        sys.exit(f"could not locate Ruby Gem.bindir ({exc}); is the `cddl` gem installed?")
    binary = os.path.join(bindir, "cddl")
    if not os.path.exists(binary):
        sys.exit(f"`cddl` gem binary not found at {binary}; run `gem install cddl`")
    return binary


def validate(binary: str, path: str) -> tuple[bool, str]:
    proc = subprocess.run(
        [binary, CDDL, "validate", path],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return True, ""
    # The gem dumps a large diagnostic tree; keep the headline.
    first = (proc.stdout + proc.stderr).strip().splitlines()
    return False, (first[0] if first else f"exit {proc.returncode}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("globs", nargs="*", default=["out/*.vcon.json", "examples/*.vcon.json"])
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    binary = gem_cddl_bin()
    files = sorted({f for g in args.globs for f in glob.glob(g, recursive=True)})
    if not files:
        sys.exit("no files matched")

    results = []
    n_ok = 0
    for f in files:
        ok, msg = validate(binary, f)
        results.append({"file": os.path.relpath(f, HERE), "valid": ok, "error": msg})
        n_ok += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {os.path.relpath(f, HERE)}"
              + (f"  {msg}" if not ok else ""))

    print(f"\n{n_ok}/{len(files)} valid against schema/vcon.cddl (Ruby cddl gem)")
    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump(results, fh, indent=2)
    return 0 if n_ok == len(files) else 1


if __name__ == "__main__":
    raise SystemExit(main())
