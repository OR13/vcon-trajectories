# vcon-trajectories

**Can real agent trajectories be represented as IETF vCons?** Yes. This repo
started by converting "mythos" model trajectories and now maps **eight real,
public agent-trajectory sources** (plus one gated dataset) into
[IETF vCon](https://datatracker.ietf.org/group/vcon/documents/) containers
(`draft-ietf-vcon-vcon-core-03`, container version **0.4.0**) and validates every
one against both the draft's **JSON Schema** and a **CDDL** grammar.

```
43/43 public vCons valid against the vCon JSON Schema (v0.4.0) AND the CDDL grammar.
```

## Scope — what's covered

- **Target:** vCon **0.4.0 core** (`draft-ietf-vcon-vcon-core-03`) — parties,
  dialog, analysis, attachments. **Not** the (draft) `agent_session`/VAC
  extension (see [caveats](#caveats--scope)).
- **Sources:** the Qwythos Mythos eval logs + 7 public trajectory datasets
  (coding, tool-use, web/GUI, telemetry) + a publishable synthetic sample + the
  gated `VINAY-UMRETHE/Mythos-Agent`. See the coverage matrix in
  [`docs/trajectory-sources.md`](docs/trajectory-sources.md) and the feature
  rubric in [`docs/trajectory-feature-space.md`](docs/trajectory-feature-space.md).
- **Feature coverage:** multi-turn & long-horizon, multi-agent, tool calls +
  results + **parallel** calls + **errors**, reasoning/chain-of-thought,
  reward/outcome labels, **real per-turn timestamps**, GUI action+observation,
  telemetry span-trees, and **binary/external** content.
- **Validation:** JSON Schema (with `uuid`/`date-time` format checks) **and** CDDL
  (Ruby `cddl` gem). Negative controls are rejected.
- **Two mappings are conventions, not standard.** Agent **handoff → `transfer`**
  and **aborted run → `incomplete`/`disposition`** reuse telephony constructs;
  these are clearly labeled as *this project's* interpretation, **not** an
  IETF-defined mapping — see [`docs/conventions.md`](docs/conventions.md) and
  [`examples/conventions/`](examples/conventions/) (each such vCon embeds the
  disclaimer inline).

## What this demonstrates

Agent trajectories — a prompt, the model's chain-of-thought, its tool calls, the
tool results, and the final answer — map cleanly onto the vCon conversation model:

| Trajectory concept | vCon representation |
|--------------------|---------------------|
| the human prompt / the model / each tool | `parties[]` (`type` person / bot / bot) |
| every message & tool call/result, in order | `dialog[]` (`type: "text"`, with `originator`) |
| the model's reasoning (chain-of-thought) | `analysis[]` (`type: "report"`, `schema: "chain-of-thought"`) |
| per-trajectory eval metadata | `analysis[]` (`type: "report"`, `schema: "qwythos-eval"`) |
| the tool definitions available | `attachments[]` (`purpose: "tool-definitions"`) |

Full design: [`docs/mapping.md`](docs/mapping.md). vCon object-model notes:
[`docs/vcon-spec-notes.md`](docs/vcon-spec-notes.md).

## The data

The source is `empero-ai/Qwythos-9B-Claude-Mythos-5-1M` — a Mythos-fine-tuned
model. Its *training* traces are proprietary, but its **public eval logs** are
real trajectories and are what we convert:

- `evals/tool_test_outputs.md` → 7 multi-round tool-use trajectories
- `evals/sample_generations.md` → 25 single-turn reasoning+answer generations

They are already vendored under [`data/qwythos_evals/`](data/qwythos_evals/), and
[`docs/data-source.md`](docs/data-source.md) documents exactly how to (re)download
them (no auth needed). It also covers a **separate, unrelated** structured HF
dataset, the gated [`VINAY-UMRETHE/Mythos-Agent`](https://huggingface.co/datasets/VINAY-UMRETHE/Mythos-Agent)
(CC-BY-4.0) — note that is *not* the Qwythos model's training data, just another
"mythos"-named artifact.

## A publishable example

Because the `VINAY-UMRETHE/Mythos-Agent` dataset is gated, the vCons derived from
it are git-ignored (not republished here). Instead,
[`examples/mythos_agent_sample.vcon.json`](examples/mythos_agent_sample.vcon.json)
is a **publishable** vCon built from a synthetic record
([`examples/mythos_agent_sample_record.json`](examples/mythos_agent_sample_record.json))
that uses the dataset's *exact schema* and the *same* `mythos.record_to_vcon`
converter. It is structurally identical to the gated-derived vCons (verified in
tests) but contains only original, shareable content.

```bash
PYTHONPATH=src python examples/generate_sample.py   # regenerate + validate the sample
```

## Multi-source coverage

Beyond the Mythos data, the repo maps **seven real, public agent-trajectory
sources** into vCon 0.4.0 to exercise the whole [trajectory feature
space](docs/trajectory-feature-space.md) — see [`docs/trajectory-sources.md`](docs/trajectory-sources.md)
for the full coverage matrix. Each source has a small adapter
([`src/vcon_trajectories/sources/`](src/vcon_trajectories/sources/)) that
normalizes it into one shared representation, then a single converter emits vCon.

| Source | Exercises |
|--------|-----------|
| sierra-research/tau-bench | user-simulator ↔ agent ↔ tools; **reward** labels |
| nebius/SWE-rebench-openhands-trajectories | **long-horizon** code-exec; `resolved`/`exit_status`; reasoning |
| trace-commons/agent-traces | **real per-turn timestamps**; **real tool errors** (`is_error`) |
| NousResearch/hermes-function-calling-v1 | **parallel tool calls**; tool defs |
| osunlp/Mind2Web | **GUI actions + DOM observations** |
| liminghao1630/API-Bank | structured API calls; multi-user-turn |
| Arize Phoenix / OpenInference | **telemetry span-tree** → flat dialog |

A committed example vCon per source lives in [`examples/sources/`](examples/sources/)
(with [`ATTRIBUTION.md`](examples/sources/ATTRIBUTION.md)); all are valid against
both the JSON Schema and the CDDL. Regenerate: `python scripts/build_source_examples.py`.

### Convention demonstrators (non-standard mappings — clearly labeled)

Three rarer features are shown in [`examples/conventions/`](examples/conventions/).
Two of them **reuse vCon telephony constructs** and are **conventions of this
project, not IETF-defined mappings** — each vCon embeds the disclaimer inline and
[`docs/conventions.md`](docs/conventions.md) draws the standard-vs-convention line:

| Feature | vCon construct | Standard? | Data |
|---|---|---|---|
| agent → agent handoff | `dialog.type:"transfer"` | **convention** | real (Who&When / Magentic-One) |
| aborted / failed run leg | `dialog.type:"incomplete"` + `disposition` | **convention** | synthetic |
| large / binary content | external `url`+`content_hash`, `base64url` | standard (illustrative data) | real DOM + placeholder image |

Regenerate: `python scripts/build_convention_examples.py`.

## Validation

Primary validation is against the **authoritative JSON Schema** shipped in
Appendix B of the core draft ([`schema/vcon_json_schema.json`](schema/vcon_json_schema.json),
JSON-Schema draft-07, `vcon` const `0.4.0`), using `jsonschema` with format
assertions for `uuid` and `date-time`.

As a secondary cross-check we round-trip through the IETF reference
implementation, [`python-vcon`](https://github.com/py-vcon/py-vcon). Caveat:
**python-vcon only speaks vCon 0.0.2**, which predates the draft's 0.4.0 and ships
no JSON Schema of its own — so it can only parse a version-downgraded *copy*. The
authoritative check here is the JSON Schema.

## CDDL validation report

Every generated vCon is *also* validated against a CDDL grammar
([`schema/vcon.cddl`](schema/vcon.cddl)) — a corpus-informed
[RFC 8610](https://www.rfc-editor.org/rfc/rfc8610) definition of the vCon
container that accepts the spec's `vcon` values `0.0.1 / 0.0.2 / 0.4.0` and, per
its own annotations, relaxes a few points to match real-world corpus practice.

- **Tool:** the Ruby `cddl` gem **0.12.14** (Bormann's RFC 8610 reference
  implementation — the tool this grammar's `.cat`/`.regexp`/socket features
  target). On PATH it is often shadowed by the Rust `cddl` crate, so the runner
  resolves the gem binary via `Gem.bindir`.
- **Reproduce:** `gem install cddl` then
  `python scripts/cddl_validate.py "out/*.vcon.json" "examples/*.vcon.json"`

**Results (2026-07-18):**

| Set | Files | Result |
|-----|-------|--------|
| Qwythos trajectories (`out/`, public) | 32 | **32/32 valid** |
| Publishable sample (`examples/`, public) | 1 | **1/1 valid** |
| Multi-source examples (`examples/sources/`, public) | 7 | **7/7 valid** |
| Convention demonstrators (`examples/conventions/`, public) | 3 | **3/3 valid** |
| Mythos-Agent dataset (`out_mythos/`, gated, local-only) | 65 | **65/65 valid** |
| **Total** | **108** | **108/108 valid** |

Run over the public examples: `python scripts/cddl_validate.py "out/*.vcon.json" "examples/**/*.vcon.json"` (43/43).

The check is meaningful, not vacuous — negative controls are rejected by the
grammar: missing `created_at`, missing `parties`, a non-RFC-3339 `created_at`,
and a `vcon` version outside the enum all fail validation.

> The 65 gated-dataset vCons are validated locally (they are git-ignored and not
> published here); the counts above are reported for completeness.

## Quick start

```bash
uv venv --python 3.11 && source .venv/bin/activate   # any 3.9–3.12
uv pip install -e .                                   # core deps
python -m vcon_trajectories                           # parse → convert → validate → write out/
```

Options: `--data-dir`, `--out-dir`, `--schema`, `--no-pyvcon`. Generated vCons
land in [`out/`](out/). To also run the reference cross-check, install the extra
(needs Python < 3.13): `uv pip install -e '.[reference]'`.

### Tests

```bash
uv pip install pytest
PYTHONPATH=src pytest
```

## Layout

```
schema/   vCon JSON Schema (Appendix B), vcon.cddl grammar, + core-03 draft text
data/     vendored Qwythos eval logs (the trajectories)
docs/     spec notes, mapping, feature-space rubric, source catalog, conventions
examples/ publishable sample; sources/ (7 per-source vCons); conventions/ (3)
scripts/  cddl_validate.py, build_source_examples.py, build_convention_examples.py
src/vcon_trajectories/
          parse.py    Qwythos eval markdown → Trajectory objects (tolerant)
          convert.py  Trajectory → vCon 0.4.0 dict (+ uuid/timestamp helpers)
          mythos.py   VINAY-UMRETHE/Mythos-Agent (gated) → vCon 0.4.0
          sources/    ir.py (shared IR + converter) + adapters.py (8 adapters)
          validate.py jsonschema validation + python-vcon cross-check
          __main__.py the end-to-end Qwythos pipeline / CLI
out/      generated, schema-valid .vcon.json files
tests/    pipeline + multi-source + convention tests (19)
```

## Experimental (separate track): `agent_session` / VAC

> Kept deliberately apart from the core mapping above. See
> [`experiments/vac-agent-session/`](experiments/vac-agent-session/).

A **prototype** maps the shared IR to the IETF `agent_session` vCon extension
(`draft-howe-vcon-agent-session`) with an embedded **VAC** record
(`draft-birkholz-verifiable-agent-conversations`). Both are **individual
Internet-Drafts at `-00`, not adopted WG documents** — this is exploratory and
does not affect the core deliverable. The prototype's outer vCons validate against
the core schema/CDDL and the embedded VAC records validate against the VAC draft's
own CDDL. It does **not** implement the signed (COSE_Sign1) form. Details, exact
draft status, and mapping choices: [`experiments/vac-agent-session/SPEC.md`](experiments/vac-agent-session/SPEC.md).

## Caveats & scope

- **Core only; two mappings are conventions.** Output targets vCon **0.4.0 core**.
  This is **not** the (draft) `agent_session` / Verifiable Agent Conversations
  extension — the IETF's purpose-built target for agent traces (see
  [`docs/trajectory-sources.md`](docs/trajectory-sources.md)). The **handoff →
  `transfer`** and **aborted-run → `incomplete`** mappings reuse telephony
  constructs and are **this project's convention, not IETF-endorsed**
  ([`docs/conventions.md`](docs/conventions.md)). The adopted WG extensions
  (contact-center, privacy-primer) are noted in the spec notes but not exercised.
- **Timestamps.** Some sources carry **real** per-turn timestamps (agent-traces,
  OpenInference, Mythos-Agent `created_at`); where a source has none, message
  *order* is preserved and `dialog.start` is a synthesized monotonic offset.
- **Truncated JSON** in the Qwythos logs is preserved raw (`_raw_arguments` /
  `_raw_result`) rather than dropped; the vCon stays valid.
- **UUIDs** are deterministic (hash of source identity) for diff-friendly output;
  version bits mark them UUIDv8 as the draft recommends.
- **Illustrative data** in `examples/conventions/external-and-binary-content.vcon.json`:
  the external `url` does not dereference to the hashed bytes (the `content_hash`
  is a real SHA-512) and the image is a placeholder — labeled inline.
- **Fidelity.** The Mythos-Agent mapping is lossless (verified content round-trip);
  per-source example vCons may be sliced for size (noted in their `analysis`).
