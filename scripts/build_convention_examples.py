#!/usr/bin/env python3
"""Build the *convention* demonstrator vCons under examples/conventions/.

These exercise vCon constructs whose APPLICATION to agent trajectories is a
convention of this project, NOT an IETF-defined mapping (see docs/conventions.md).
Each output embeds a `mapping-note` analysis entry stating this plainly.

    python scripts/build_convention_examples.py
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from vcon_trajectories.sources import adapters as A            # noqa: E402
from vcon_trajectories.sources.ir import (INCOMPLETE, MESSAGE, OBSERVATION,      # noqa: E402
                                          TOOL_CALL, Turn, UTrajectory,
                                          content_hash_sri, utrajectory_to_vcon)
from vcon_trajectories.validate import make_validator, validate_vcon  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "examples", "conventions")

# A real, minimal 1x1 PNG used as an ILLUSTRATIVE binary artifact.
_PNG_1x1 = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
            b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")


def _get(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def hf_rows(dataset, config="default", split="train", length=1, offset=0):
    url = (f"https://datasets-server.huggingface.co/rows?dataset={urllib.request.quote(dataset)}"
           f"&config={config}&split={split}&offset={offset}&length={length}")
    return [r["row"] for r in json.loads(_get(url))["rows"]]


def add_mapping_note(vcon, note):
    vcon["analysis"].append({
        "type": "report", "vendor": "vcon-trajectories", "schema": "mapping-note",
        "dialog": list(range(len(vcon["dialog"]))), "mediatype": "text/plain",
        "body": note, "encoding": "none",
    })
    return vcon


def build():
    os.makedirs(OUT, exist_ok=True)
    validator = make_validator()
    results = []

    def emit(name, vcon):
        errs = validate_vcon(vcon, validator)
        with open(os.path.join(OUT, f"{name}.vcon.json"), "w", encoding="utf-8") as f:
            json.dump(vcon, f, indent=2, ensure_ascii=False)
        results.append((name, len(vcon["dialog"]), errs))

    # 1. Multi-agent handoff -> `transfer` (REAL data: Who&When / Magentic-One)
    ww = hf_rows("Kevin355/Who_and_When", config="Hand-Crafted")[0]
    ut = A.who_and_when(ww)
    if len(ut.turns) > 40:
        ut.metadata["example_note"] = f"sample slice: first 40 of {len(ut.turns)} turns"
        ut.turns = ut.turns[:40]
    vcon = utrajectory_to_vcon(ut)
    add_mapping_note(vcon,
        "NON-STANDARD MAPPING. Agent-to-agent handoffs in this real multi-agent "
        "trajectory (Kevin355/Who_and_When, Magentic-One) are represented with vCon's "
        "`transfer` dialog type (transferor / transfer_target / transferee). vCon "
        "`transfer` is defined by draft-ietf-vcon-vcon-core for TELEPHONY call transfer; "
        "reusing it for agent delegation is a convention of the vcon-trajectories project "
        "and is NOT defined or endorsed by the IETF vCon working group. transferor = the "
        "delegating agent, transfer_target = the receiving agent, transferee = the user/"
        "task party (an approximation). See docs/conventions.md.")
    emit("multi-agent-transfer", vcon)

    # 2. Aborted run -> `incomplete` + `disposition` (SYNTHETIC, clearly labeled)
    ut = UTrajectory(
        source="vcon-trajectories/synthetic",
        id="incomplete-demo-1",
        subject="Aborted agent run (synthetic demonstrator)",
        turns=[
            Turn(MESSAGE, "user", role="user", text="Summarize the failing test and fix it."),
            Turn(MESSAGE, "assistant", role="assistant", text="I'll run the test suite first."),
            Turn(TOOL_CALL, "assistant", role="assistant", tool_name="bash",
                 tool_input={"command": "pytest -x"}),
            Turn(INCOMPLETE, "assistant", role="assistant", disposition="failed"),
        ],
    )
    vcon = utrajectory_to_vcon(ut)
    add_mapping_note(vcon,
        "NON-STANDARD MAPPING and SYNTHETIC DATA. This trajectory was aborted before the "
        "`bash` tool call returned; the aborted leg is represented with vCon's `incomplete` "
        "dialog type and disposition \"failed\". vCon `incomplete`/`disposition` are defined "
        "by draft-ietf-vcon-vcon-core for TELEPHONY calls that did not connect "
        "(no-answer/busy/congestion/failed/hung-up/voicemail-no-message); \"failed\" is the "
        "only enum value that reasonably fits an aborted agent run. Reusing this construct "
        "for agent trajectories is a convention of the vcon-trajectories project, NOT an "
        "IETF-defined mapping. This record is synthetic. See docs/conventions.md.")
    emit("incomplete-run", vcon)

    # 3. External artifact + inline binary (STANDARD mechanisms, ILLUSTRATIVE data)
    dom = (hf_rows("osunlp/Mind2Web")[0]["actions"][0].get("cleaned_html") or "").encode("utf-8")
    ut = UTrajectory(
        source="osunlp/Mind2Web",
        id="external-binary-demo-1",
        subject="Large DOM as external content + a screenshot as base64url (illustrative)",
        turns=[
            Turn(MESSAGE, "user", role="user", text="Book a table on this page."),
            Turn(OBSERVATION, "environment", role="environment",
                 url="https://example.invalid/mind2web/dom/action-0.html",
                 content_hash=content_hash_sri(dom), mediatype="text/html",
                 meta={"note": "illustrative url; content_hash is the real SHA-512 of the DOM"}),
            Turn(OBSERVATION, "environment", role="environment",
                 binary=_PNG_1x1, mediatype="image/png",
                 meta={"note": "illustrative 1x1 PNG artifact"}),
            Turn(MESSAGE, "assistant", role="assistant", text="I can see the reservation form; clicking Book."),
        ],
    )
    vcon = utrajectory_to_vcon(ut)
    add_mapping_note(vcon,
        "STANDARD vCon MECHANISMS, ILLUSTRATIVE DATA. A large web DOM (real bytes from "
        "osunlp/Mind2Web) is represented as EXTERNAL content via `url` + `content_hash` "
        "(dereferenced content), and a binary screenshot artifact via `encoding`:\"base64url\" "
        "— both are standard, spec-defined vCon content mechanisms. Caveats: the `url` is "
        "ILLUSTRATIVE and does not dereference to the hashed bytes (the `content_hash` is a "
        "real SHA-512 of the included DOM); the PNG is a placeholder 1x1 image. See "
        "docs/conventions.md.")
    emit("external-and-binary-content", vcon)

    ok = 0
    for name, nd, errs in results:
        status = "VALID" if not errs else f"INVALID {errs[:1]}"
        ok += not errs
        print(f"{name:30} dialog={nd:>3}  {status}")
    print(f"\n{ok}/{len(results)} valid; written to examples/conventions/")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(build())
