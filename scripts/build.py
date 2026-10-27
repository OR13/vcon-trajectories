#!/usr/bin/env python3
"""Convert real public trajectories -> ai_agent vCons, validate, write examples + report.

    python scripts/build.py                 # committed examples (small, capped)
    python scripts/build.py --report        # also run the multi-session corpus sweep
                                            # and write docs/corpus-report.md
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import corpora as C  # noqa: E402
from vcon_trajectories.ai_agent import utrajectory_to_vcon  # noqa: E402
from vcon_trajectories.coverage import FEATURES, features  # noqa: E402
from vcon_trajectories.native import atif as atif_native  # noqa: E402
from vcon_trajectories.native import claude_code, codex, gemini_cli  # noqa: E402
from vcon_trajectories.sources import adapters as A  # noqa: E402
from vcon_trajectories.validate import CddlValidator, semantic_issues  # noqa: E402

OUT = os.path.join(HERE, "examples")
MAXSTR = 1500
_HOME = re.compile(r"/(Users|home)/[^/\"\\\s]+")
_EMAIL = re.compile(r"(?<![\w@.])(?!git@)[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def scrub(text: str) -> str:
    """Examples are committed: drop home-directory user names and e-mail addresses."""
    return _EMAIL.sub("redacted@example.invalid", _HOME.sub(r"/\1/USER", text))


def shrink(x, n=MAXSTR):
    if isinstance(x, str):
        return x if len(x) <= n else x[:n] + f"…[truncated for example; {len(x)} chars]"
    if isinstance(x, list):
        return [shrink(i, n) for i in x]
    if isinstance(x, dict):
        return {k: shrink(v, n) for k, v in x.items()}
    return x


def cap(ut, n):
    if len(ut.turns) > n:
        ut.metadata["example_note"] = f"sample slice: first {n} of {len(ut.turns)} turns; long strings truncated"
        ut.turns = ut.turns[:n]
    return ut


def write(path, vcon):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(scrub(json.dumps(vcon, indent=2, ensure_ascii=False)) + "\n")


def get_hf_rows(dataset, config="default", split="train", length=1):
    q = f"https://datasets-server.huggingface.co/rows?dataset={dataset}&config={config}&split={split}&offset=0&length={length}"
    return [r["row"] for r in json.loads(C.get(q))["rows"]]


def examples(v):
    """(vendor, name, UTrajectory, turn cap) for the committed examples."""
    out = []
    n, recs = next(C.agent_traces_claude(1))
    out.append(("anthropic", "claude-code-agent-traces", claude_code.parse(recs, source="trace-commons/agent-traces"), 60))
    for sid, recs in C.swechat_native("Claude Code", 1, max_turns=40):
        out.append(("anthropic", "claude-code-swe-chat", claude_code.parse(recs, source="SALT-NLP/SWE-chat"), 60))
    for sid, recs in C.swechat_native("Codex", 1, max_turns=8):
        out.append(("openai", "codex-cli-swe-chat", codex.parse(recs, source="SALT-NLP/SWE-chat"), 60))
    for sid, rows in C.swechat_gemini(1):
        out.append(("google", "gemini-cli-swe-chat", gemini_cli.parse(rows, source="SALT-NLP/SWE-chat"), 60))
    # Harbor ATIF (an independent producer of the same trajectory idea)
    for tid, a in C.tb2_atif(1):
        out.append(("other", "terminal-bench-2-atif", atif_native.parse_trajectory(a, id=tid, source="AlienKevin/marin-8b-tb2-eval-traces"), 40))
    # benchmark / framework corpora
    tb = json.loads(C.get("https://raw.githubusercontent.com/sierra-research/tau-bench/main/historical_trajectories/gpt-4o-airline.json"))
    out.append(("other", "tau-bench", A.tau_bench(tb[0]), 40))
    out.append(("other", "swe-rebench-openhands", A.swe_rebench(get_hf_rows("nebius/SWE-rebench-openhands-trajectories")[0]), 40))
    out.append(("other", "hermes-function-calling", A.hermes(get_hf_rows("NousResearch/hermes-function-calling-v1", "func_calling")[0]), 60))
    m = get_hf_rows("osunlp/Mind2Web")[0]
    m["actions"], m["action_reprs"] = (m.get("actions") or [])[:2], (m.get("action_reprs") or [])[:2]
    out.append(("other", "mind2web", A.mind2web(m), 40))
    ab_url = ("https://raw.githubusercontent.com/AlibabaResearch/DAMO-ConvAI/main/api-bank/"
              "lv1-lv2-samples/level-1-given-desc/AddAgenda-AddAlarm-GetUserToken-level-2-1.jsonl")
    out.append(("other", "api-bank", A.api_bank(C.jsonl(C.get(ab_url)), "AddAgenda-AddAlarm-GetUserToken-level-2-1"), 40))
    spans = C.jsonl(C.get("https://storage.googleapis.com/arize-phoenix-assets/traces/random.jsonl"))[:6]
    out.append(("other", "openinference", A.openinference(spans, "phoenix-random-6"), 40))
    return out


def sweep(v):
    """Many sessions per vendor-native corpus -> per-corpus pass rates + feature coverage."""
    jobs = [
        ("Claude Code · trace-commons/agent-traces", "anthropic",
         lambda: ((s, claude_code.parse(r, source="trace-commons/agent-traces")) for s, r in C.agent_traces_claude(40))),
        ("Claude Code · SWE-chat", "anthropic",
         lambda: ((s, claude_code.parse(r, source="SALT-NLP/SWE-chat")) for s, r in C.swechat_native("Claude Code", 25, 60))),
        ("Codex CLI · SWE-chat", "openai",
         lambda: ((s, codex.parse(r, source="SALT-NLP/SWE-chat")) for s, r in C.swechat_native("Codex", 25, 40))),
        ("Gemini CLI · SWE-chat (normalized rows)", "google",
         lambda: ((s, gemini_cli.parse(r)) for s, r in C.swechat_gemini(8))),
        ("Harbor ATIF · Terminal-Bench 2.0 (terminus-2)", "harbor",
         lambda: ((s, atif_native.parse_trajectory(a, id=s, source="AlienKevin/marin-8b-tb2-eval-traces")) for s, a in C.tb2_atif())),
    ]
    rows = []
    for name, vendor, gen in jobs:
        n = ok = 0
        feats = Counter()
        fails = []
        stats = Counter()
        sysev = Counter()
        for sid, ut in gen():
            vc = utrajectory_to_vcon(ut)
            good, msg = v.validate(vc)
            issues = semantic_issues(vc)
            n += 1
            ok += good and not issues
            if not good or issues:
                fails.append((sid, msg or issues[:2]))
            for f in features(vc):
                feats[f] += 1
            for e in vc.get("events", []):
                if e["type"] == "system-event":
                    sysev[e["event_type"]] += 1
            stats["events"] += len(vc.get("events", []))
            stats["dialog"] += len(vc.get("dialog", []))
            for k, c in (ut.metadata.get("native_records_not_mapped") or {}).items():
                stats[f"unmapped:{k}"] += c
        rows.append(dict(name=name, vendor=vendor, n=n, ok=ok, feats=dict(feats), fails=fails, stats=dict(stats), sysev=dict(sysev)))
        print(f"  {name}: {ok}/{n} valid", flush=True)
    return rows


def report(rows):
    L = ["# Corpus validation report", "",
         "Generated by `python scripts/build.py --report`. Every session is converted with the vendor-native parser, "
         "composed into an `ai_agent` vCon, and validated with the pinned draft CDDL "
         "(`schema/ai-agent/PINNED.md`) via the Ruby `cddl` gem, plus the semantic checks CDDL cannot express.", "",
         "## Validity", "", "| Corpus | Vendor harness | Sessions | Valid | Events | Dialogs |", "|---|---|--:|--:|--:|--:|"]
    for r in rows:
        L.append(f"| {r['name']} | {r['vendor']} | {r['n']} | {r['ok']} | {r['stats'].get('events', 0)} | {r['stats'].get('dialog', 0)} |")
    L += ["", "## Draft constructs exercised (sessions containing the feature)", ""]
    L.append("| Construct | " + " | ".join(r["name"].split(" · ")[0] + " · " + r["name"].split(" · ")[1][:14] for r in rows) + " |")
    L.append("|---|" + "--:|" * len(rows))
    for key, label in FEATURES:
        L.append(f"| {label} | " + " | ".join(str(r["feats"].get(key, 0)) if r["feats"].get(key) else "·" for r in rows) + " |")
    L += ["", "## Native records with no mapping (counts)", ""]
    for r in rows:
        un = {k[9:]: c for k, c in r["stats"].items() if k.startswith("unmapped:")}
        if un:
            L.append(f"- **{r['name']}**: " + ", ".join(f"`{k}` ×{c}" for k, c in sorted(un.items(), key=lambda x: -x[1])[:12]))
    L += ["", "## system-event `event_type` values observed (vendor vocabulary the draft leaves open)", ""]
    for r in rows:
        if r["sysev"]:
            L.append(f"- **{r['name']}**: " + ", ".join(f"`{k}` ×{c}" for k, c in sorted(r["sysev"].items(), key=lambda x: -x[1])[:15]))
    bad = [(r["name"], f) for r in rows for f in r["fails"]]
    L += ["", "## Failures", ""] + ([f"- {n}: `{s}` — {m}" for n, (s, m) in bad] or ["None."])
    open(os.path.join(HERE, "docs", "corpus-report.md"), "w").write("\n".join(L) + "\n")
    json.dump(rows, open(os.path.join(HERE, "docs", "corpus-report.json"), "w"), indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    v = CddlValidator()
    bad = 0
    print("== committed examples ==")
    for vendor, name, ut, ncap in examples(v):
        vc = shrink(utrajectory_to_vcon(cap(ut, ncap)))
        ok, msg = v.validate(vc)
        issues = semantic_issues(vc)
        bad += (not ok) or bool(issues)
        write(os.path.join(OUT, vendor, f"{name}.vcon.json"), vc)
        print(f"  [{'PASS' if ok and not issues else 'FAIL'}] {vendor}/{name}: "
              f"{len(vc.get('dialog', []))} dialog, {len(vc.get('events', []))} events {msg} {issues[:2] or ''}")
    if args.report:
        print("== corpus sweep ==")
        report(sweep(v))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
