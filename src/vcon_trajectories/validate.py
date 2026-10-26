"""Validate vCons against the pinned draft CDDL (+ the constraints CDDL can't express).

The draft's CDDL is split across files and composed with a root rule
(`vcon-with-ai-agent = vcon`), exactly as the draft's `ai-agent.cddl` prescribes.
Validation uses the Ruby `cddl` gem (the RFC 8610 reference implementation the
draft's CDDL targets); on PATH it is often shadowed by the Rust `cddl` crate, so
the binary is resolved through `Gem.bindir`.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import json
from typing import Any, Dict, List, Tuple

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMA_DIR = os.path.join(HERE, "schema", "ai-agent")
# Order matters: the first rule is the validation root.
_PARTS = ["vcon-core", "ai-agent-vcon", "ai-agent-party", "ai-agent-session",
          "ai-agent-dialog", "ai-agent-event", "ai-agent-common"]
_ROOT = "vcon-with-ai-agent = vcon\n\n"


def compose_cddl() -> str:
    parts = [_ROOT]
    for name in _PARTS:
        with open(os.path.join(SCHEMA_DIR, f"{name}.cddl"), encoding="utf-8") as f:
            parts.append(f.read() + "\n")
    return "".join(parts)


def gem_cddl_bin() -> str:
    bindir = subprocess.check_output(["ruby", "-e", "print Gem.bindir"], text=True).strip()
    binary = os.path.join(bindir, "cddl")
    if not os.path.exists(binary):
        raise RuntimeError(f"`cddl` gem binary not found at {binary}; run `gem install cddl`")
    return binary


class CddlValidator:
    def __init__(self) -> None:
        self.binary = gem_cddl_bin()
        self._dir = tempfile.mkdtemp(prefix="vcon-cddl-")
        self.cddl_path = os.path.join(self._dir, "composed.cddl")
        with open(self.cddl_path, "w", encoding="utf-8") as f:
            f.write(compose_cddl())

    def validate_path(self, path: str) -> Tuple[bool, str]:
        p = subprocess.run([self.binary, self.cddl_path, "validate", path],
                           capture_output=True, text=True)
        if p.returncode == 0:
            return True, ""
        lines = (p.stdout + p.stderr).strip().splitlines()
        return False, (lines[0][:200] if lines else f"exit {p.returncode}")

    def validate(self, vcon: Dict[str, Any]) -> Tuple[bool, str]:
        path = os.path.join(self._dir, "in.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(vcon, f)
        return self.validate_path(path)


def semantic_issues(vcon: Dict[str, Any]) -> List[str]:
    """Constraints the CDDL comments say are 'not enforced by this CDDL'."""
    issues: List[str] = []
    n = {k: len(vcon.get(k, [])) for k in ("sessions", "parties", "dialog", "events")}
    if (n["events"] or n["dialog"]) and not n["sessions"]:
        issues.append("events/dialog present but no Session Object")
    for i, s in enumerate(vcon.get("sessions", [])):
        for p in s.get("parties", []):
            if p >= n["parties"]:
                issues.append(f"sessions[{i}].parties index {p} out of range")
        for d in s.get("dialog", []):
            if d >= n["dialog"]:
                issues.append(f"sessions[{i}].dialog index {d} out of range")
        for ref in s.get("sessions", []):
            if ref["session"] >= n["sessions"]:
                issues.append(f"sessions[{i}].sessions ref {ref['session']} out of range")
        if "start" in s:
            for d in s.get("dialog", []):
                if d < n["dialog"] and vcon["dialog"][d].get("start", "") < s["start"]:
                    issues.append(f"sessions[{i}].start is after dialog[{d}].start")
    ids = {x["entry_id"] for k in ("dialog", "events") for x in vcon.get(k, []) if "entry_id" in x}
    for k in ("dialog", "events"):
        for i, x in enumerate(vcon.get(k, [])):
            if "parent_id" in x and x["parent_id"] not in ids:
                issues.append(f"{k}[{i}].parent_id {x['parent_id']!r} matches no entry_id")
    calls = set()
    for i, e in enumerate(vcon.get("events", [])):
        if e["session"] >= n["sessions"]:
            issues.append(f"events[{i}].session out of range")
        if e["party"] >= n["parties"]:
            issues.append(f"events[{i}].party out of range")
        if e["type"] == "tool-call" and "call_id" in e:
            calls.add(e["call_id"])
    for i, e in enumerate(vcon.get("events", [])):
        if e["type"] == "tool-result" and "call_id" in e and e["call_id"] not in calls:
            issues.append(f"events[{i}] tool-result call_id {e['call_id']!r} has no tool-call")
    return issues
