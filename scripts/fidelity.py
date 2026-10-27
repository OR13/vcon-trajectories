#!/usr/bin/env python3
"""Round-trip fidelity: vCon(ai_agent) -> ATIF -> vCon, and vCon -> OTel GenAI spans.

For each committed example, counts what survives. `lost` is the difference in a construct
count after the round trip; `unmapped` lists vCon constructs the target format has no field for.

    python scripts/fidelity.py            # prints a table
    python scripts/fidelity.py --write    # also writes docs/fidelity.md
"""
import argparse
import glob
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "src"))

from vcon_trajectories.ai_agent import utrajectory_to_vcon  # noqa: E402
from vcon_trajectories.export.atif import to_atif  # noqa: E402
from vcon_trajectories.export.atif_check import check_atif  # noqa: E402
from vcon_trajectories.export.otel_check import check_otel  # noqa: E402
from vcon_trajectories.export.otel_genai import to_otel  # noqa: E402
from vcon_trajectories.native.atif import parse_trajectory  # noqa: E402
from vcon_trajectories.validate import CddlValidator, semantic_issues  # noqa: E402

CONSTRUCTS = ("messages", "tool-call", "tool-result", "reasoning", "token-count", "other-events",
              "input_tokens", "output_tokens", "cached_tokens", "error_flags", "call_id_pairs", "children")


def census(v):
    c = Counter()
    c["messages"] = len(v.get("dialog", []))
    for d in v.get("dialog", []):
        u = d.get("token_usage") or {}
        c["input_tokens"] += u.get("input", 0)
        c["output_tokens"] += u.get("output", 0)
        c["cached_tokens"] += u.get("cached", 0)
    calls, results = set(), set()
    for e in v.get("events", []):
        t = e["type"]
        if t == "system-event":
            if e.get("event_type") == "token-count":
                c["token-count"] += 1
                d = e.get("data") or {}
                c["input_tokens"] += d.get("input", 0) or 0
                c["output_tokens"] += d.get("output", 0) or 0
                c["cached_tokens"] += d.get("cached", 0) or 0
            else:
                c["other-events"] += 1
            continue
        c[t] += 1
        if t == "tool-call" and e.get("call_id"):
            calls.add(e["call_id"])
        if t == "tool-result":
            if e.get("call_id"):
                results.add(e["call_id"])
            if e.get("is_error"):
                c["error_flags"] += 1
    c["call_id_pairs"] = len(calls & results)
    c["children"] = max(len(v.get("sessions", [])) - 1, 0)
    return c


def run():
    rows = []
    cddl = CddlValidator()
    for f in sorted(glob.glob(os.path.join(HERE, "examples", "*", "*.vcon.json"))):
        name = os.path.relpath(f, os.path.join(HERE, "examples"))[: -len(".vcon.json")]
        v = json.load(open(f, encoding="utf-8"))
        atif = to_atif(v)
        a_err = check_atif(atif)
        back = utrajectory_to_vcon(parse_trajectory(atif, id=name, source="roundtrip"))
        ok, msg = cddl.validate(back)
        b_err = ([] if ok else [msg]) + semantic_issues(back)
        o_err = check_otel(to_otel(v))
        a, b = census(v), census(back)
        # token-count events fold into step metrics, so compare token SUMS, not event counts
        lost = {k: a[k] - b[k] for k in CONSTRUCTS if k not in ("token-count",) and a[k] != b[k]}
        rows.append((name, a, lost, a_err, b_err, o_err))
    return rows


def real_atif():
    """Independent check: real Harbor-produced ATIF -> vCon -> ATIF (Terminal-Bench 2.0, terminus-2)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import corpora as C
    cddl = CddlValidator()
    n = Counter()
    for tid, a in C.tb2_atif():
        v = utrajectory_to_vcon(parse_trajectory(a, id=tid, source="AlienKevin/marin-8b-tb2-eval-traces"))
        b = to_atif(v)
        ok, _ = cddl.validate(v)
        f = lambda t, k: sum(len(s.get(k) or []) for s in t["steps"])
        pt = lambda t: sum((s.get("metrics") or {}).get("prompt_tokens", 0) for s in t["steps"])
        n["trajectories"] += 1
        n["native ATIF passes check"] += not check_atif(a)
        n["vCon passes CDDL + semantic"] += ok and not semantic_issues(v)
        n["re-exported ATIF passes check"] += not check_atif(b)
        n["step count preserved"] += len(a["steps"]) == len(b["steps"])
        n["tool_calls preserved"] += f(a, "tool_calls") == f(b, "tool_calls")
        n["prompt_tokens preserved"] += pt(a) == pt(b)
        n["steps"] += len(a["steps"])
    return n


def render_real(n):
    t = n["trajectories"]
    out = [f"## Real Harbor ATIF round trip ({t} Terminal-Bench 2.0 trajectories, {n['steps']} steps)", "",
           "ATIF-v1.6 produced by Harbor's `terminus-2` agent, ATIF -> vCon (`ai_agent`) -> ATIF. "
           "Source: AlienKevin/marin-8b-tb2-eval-traces (Apache-2.0).", "", "| check | trajectories |", "|---|--:|"]
    out += [f"| {k} | {n[k]}/{t} |" for k in n if k not in ("trajectories", "steps")]
    return "\n".join(out)


def render(rows):
    out = ["| example | messages | tool-call | tool-result | reasoning | in/out/cached tokens | ATIF | back to vCon | OTel |",
           "|---|--:|--:|--:|--:|---|---|---|---|"]
    for name, a, lost, a_err, b_err, o_err in rows:
        tok = f"{a['input_tokens']}/{a['output_tokens']}/{a['cached_tokens']}"
        out.append(f"| {name} | {a['messages']} | {a['tool-call']} | {a['tool-result']} | {a['reasoning']} | {tok} | "
                   f"{'valid' if not a_err else str(len(a_err)) + ' errors'} | "
                   f"{'valid' if not b_err else str(len(b_err)) + ' errors'} | "
                   f"{'valid' if not o_err else str(len(o_err)) + ' errors'} |")
    out += ["", "Constructs lost in vCon -> ATIF -> vCon (difference in construct counts; preserved = counts, token sums and call/result pairing match, not byte equality):", ""]
    for name, a, lost, *_ in rows:
        out.append(f"- `{name}`: " + (", ".join(f"{k} {d:+d}" for k, d in lost.items()) if lost else "preserved"))
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    text = render(run()) + "\n\n" + render_real(real_atif())
    print(text)
    if args.write:
        with open(os.path.join(HERE, "docs", "fidelity.md"), "w", encoding="utf-8") as f:
            f.write("# Format fidelity\n\nGenerated by `scripts/fidelity.py` from `examples/`. "
                    "ATIF check = `export/atif_check.py` (RFC rules re-implemented; not Harbor's validator). "
                    "OTel check = `export/otel_check.py`.\n\n" + text + "\n")
