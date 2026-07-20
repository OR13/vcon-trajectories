#!/usr/bin/env python3
"""Fetch one representative real record per source (public routes, no auth),
convert via the shared adapters + IR, validate against the vCon JSON Schema, and
write a small example vCon per source to examples/sources/.

    python scripts/build_source_examples.py

Records are sliced to keep committed examples small; the full-size conversions are
exercised in tests. Only derived vCons are written here (see ATTRIBUTION.md); raw
datasets are not vendored.
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from vcon_trajectories.sources import adapters as A          # noqa: E402
from vcon_trajectories.sources.ir import utrajectory_to_vcon  # noqa: E402
from vcon_trajectories.validate import make_validator, validate_vcon  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "examples", "sources")


def _get(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def hf_rows(dataset, config="default", split="train", length=1, offset=0):
    url = (f"https://datasets-server.huggingface.co/rows?dataset={urllib.request.quote(dataset)}"
           f"&config={config}&split={split}&offset={offset}&length={length}")
    return [r["row"] for r in json.loads(_get(url))["rows"]]


def cap_turns(ut, n):
    """Slice to the first n turns (keep examples small); note the truncation."""
    if len(ut.turns) > n:
        ut.metadata["example_note"] = f"sample slice: first {n} of {len(ut.turns)} turns"
        ut.turns = ut.turns[:n]
    return ut


def truncate_observations(vcon, limit=3000):
    """Shrink very large inline observation bodies (e.g. Mind2Web DOM) so the
    committed example stays small; records the original length."""
    for d in vcon["dialog"]:
        b = d.get("body")
        if d.get("encoding") == "none" and isinstance(b, str) and len(b) > limit:
            d["meta"] = {"truncated": True, "full_length": len(b)}
            d["body"] = b[:limit] + f"\n…[truncated for example; {len(b)} chars total]"
    return vcon


def build():
    os.makedirs(OUT, exist_ok=True)
    validator = make_validator()
    results = []

    def emit(name, ut, post=None):
        vcon = utrajectory_to_vcon(ut)
        if post:
            vcon = post(vcon)
        errors = validate_vcon(vcon, validator)
        path = os.path.join(OUT, f"{name}.vcon.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(vcon, f, indent=2, ensure_ascii=False)
        results.append((name, ut.source, len(vcon["parties"]), len(vcon["dialog"]), errors))

    # 1. tau-bench (GitHub, MIT) — reward, user-simulator, tools
    tb = json.loads(_get("https://raw.githubusercontent.com/sierra-research/tau-bench/main/historical_trajectories/gpt-4o-airline.json"))
    emit("tau-bench", cap_turns(A.tau_bench(tb[0]), 40))

    # 2. SWE-rebench (HF, CC-BY-4.0) — long-horizon coding, resolved/exit_status, reasoning
    emit("swe-rebench", cap_turns(A.swe_rebench(hf_rows("nebius/SWE-rebench-openhands-trajectories")[0]), 40))

    # 3. agent-traces (HF, CC-BY-4.0) — REAL timestamps + real tool errors (is_error)
    emit("agent-traces", cap_turns(A.agent_traces(hf_rows("trace-commons/agent-traces")[0]), 100))

    # 4. Hermes function-calling (HF, Apache-2.0) — parallel tool calls, tool defs
    emit("hermes-function-calling", A.hermes(hf_rows("NousResearch/hermes-function-calling-v1", config="func_calling")[0]))

    # 5. Mind2Web (HF, CC-BY-4.0) — GUI actions + DOM observations
    m = hf_rows("osunlp/Mind2Web")[0]
    m["actions"] = (m.get("actions") or [])[:2]
    m["action_reprs"] = (m.get("action_reprs") or [])[:2]
    emit("mind2web", A.mind2web(m), post=truncate_observations)

    # 6. API-Bank (GitHub, MIT) — structured API calls, multi-user-turn dialogue
    ab_url = ("https://raw.githubusercontent.com/AlibabaResearch/DAMO-ConvAI/main/api-bank/"
              "lv1-lv2-samples/level-1-given-desc/AddAgenda-AddAlarm-GetUserToken-level-2-1.jsonl")
    ab = [json.loads(l) for l in _get(ab_url).decode().splitlines() if l.strip()]
    emit("api-bank", A.api_bank(ab, "AddAgenda-AddAlarm-GetUserToken-level-2-1"))

    # 7. OpenInference / Phoenix (public GCS) — telemetry spans -> flattened dialog
    spans = [json.loads(l) for l in _get("https://storage.googleapis.com/arize-phoenix-assets/traces/random.jsonl").decode().splitlines() if l.strip()][:6]
    emit("openinference", A.openinference(spans, "phoenix-random-6"))

    print(f"{'source':16} {'dataset':45} parties dialog  status")
    ok = 0
    for name, src, np, nd, errs in results:
        status = "VALID" if not errs else f"INVALID {errs[:1]}"
        ok += not errs
        print(f"{name:16} {src:45} {np:>5} {nd:>6}  {status}")
    print(f"\n{ok}/{len(results)} valid; written to examples/sources/")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(build())
