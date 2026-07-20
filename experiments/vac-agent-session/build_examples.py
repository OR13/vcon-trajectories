#!/usr/bin/env python3
"""Build EXPERIMENTAL agent_session/VAC examples from real trajectories.

    python experiments/vac-agent-session/build_examples.py

Emits, per source, an `agent_session`-extended vCon (*.vcon.json) whose
`analysis[0].body` is an embedded VAC verifiable-agent-record, plus the record on
its own (*.vac.json) for CDDL validation. Outer vCons are validated against the
core vCon JSON Schema (they remain valid core vCons + extension fields).
"""
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vac import (utrajectory_to_agent_session_vcon, utrajectory_to_vac)  # noqa: E402
from vcon_trajectories.sources import adapters as A                       # noqa: E402
from vcon_trajectories.validate import make_validator, validate_vcon      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "examples")


def _get(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def hf_rows(dataset, config="default", split="train", length=1, offset=0):
    url = (f"https://datasets-server.huggingface.co/rows?dataset={urllib.request.quote(dataset)}"
           f"&config={config}&split={split}&offset={offset}&length={length}")
    return [r["row"] for r in json.loads(_get(url))["rows"]]


def cap(ut, n):
    if len(ut.turns) > n:
        ut.metadata["example_note"] = f"sample slice: first {n} of {len(ut.turns)} turns"
        ut.turns = ut.turns[:n]
    return ut


def main():
    os.makedirs(OUT, exist_ok=True)
    validator = make_validator()
    results = []

    def emit(name, vcon, vac):
        errs = validate_vcon(vcon, validator)
        json.dump(vcon, open(os.path.join(OUT, f"{name}.vcon.json"), "w"), indent=2, ensure_ascii=False)
        json.dump(vac, open(os.path.join(OUT, f"{name}.vac.json"), "w"), indent=2, ensure_ascii=False)
        results.append((name, len(vcon["dialog"]), len(vac["session"]["entries"]), errs))

    # A) Claude Code session (real timestamps, model, env, tool errors)
    rec = hf_rows("trace-commons/agent-traces")[0]
    model, env = None, {}
    for e in rec.get("trace", []):
        m = e.get("message") or {}
        if not model and isinstance(m, dict) and m.get("model"):
            model = m["model"]
        if e.get("cwd") and "cwd" not in env:
            env["cwd"] = e["cwd"]
        if e.get("gitBranch") and "vcs_branch" not in env:
            env["vcs_branch"] = e["gitBranch"]
    ut = cap(A.agent_traces(rec), 60)
    kw = dict(model_id=model or "claude (unknown)", provider="anthropic",
              recording_agent=(rec.get("harness") or "").replace("_", "-") or None,
              environment=env or None)
    emit("agent-session-claude-code",
         utrajectory_to_agent_session_vcon(ut, agent_name=model, **kw),
         utrajectory_to_vac(ut, model_id=kw["model_id"], model_provider="anthropic",
                            cli_name=kw["recording_agent"], environment=env or None,
                            recording_agent={"name": kw["recording_agent"]} if kw["recording_agent"] else None))

    # B) tau-bench (gpt-4o / openai)
    tb = json.loads(_get("https://raw.githubusercontent.com/sierra-research/tau-bench/main/historical_trajectories/gpt-4o-airline.json"))[0]
    ut = cap(A.tau_bench(tb), 40)
    emit("agent-session-taubench",
         utrajectory_to_agent_session_vcon(ut, model_id="gpt-4o", provider="openai",
                                           agent_name="gpt-4o", recording_agent="tau-bench"),
         utrajectory_to_vac(ut, model_id="gpt-4o", model_provider="openai", cli_name="tau-bench"))

    ok = 0
    for name, nd, ne, errs in results:
        status = "VALID (core)" if not errs else f"INVALID {errs[:1]}"
        ok += not errs
        print(f"{name:30} dialog={nd:>3} vac_entries={ne:>3}  outer vCon: {status}")
    print(f"\n{ok}/{len(results)} outer vCons valid against core JSON Schema; written to examples/")
    print("NOTE: VAC records validated against agent-conversation.cddl separately (see README).")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
