# vcon-trajectories

**Can "mythos" agent trajectories from Hugging Face be represented as IETF vCons?**
Yes. This repo converts real, publicly-available Mythos-model agent trajectories
into [IETF vCon](https://datatracker.ietf.org/group/vcon/documents/) containers
(`draft-ietf-vcon-vcon-core-03`, container version **0.4.0**) and validates every
one of them against the draft's official JSON Schema.

```
32/32 trajectories valid against the vCon JSON Schema (v0.4.0), 106 dialog entries.
```

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
them (no auth needed) and how to instead use the gated `VINAY-UMRETHE/Mythos-Agent`
HF *dataset* if you prefer.

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
schema/   vCon JSON Schema (Appendix B) + the full core-03 draft text
data/     vendored Qwythos eval logs (the trajectories)
docs/     spec notes, the trajectory→vCon mapping, and data-source instructions
src/vcon_trajectories/
          parse.py    eval markdown → Trajectory objects (truncation-tolerant)
          convert.py  Trajectory → vCon 0.4.0 dict
          validate.py jsonschema validation + python-vcon cross-check
          __main__.py the end-to-end pipeline / CLI
out/      generated, schema-valid .vcon.json files
tests/    pipeline tests
```

## Caveats & scope

- **Timestamps** are synthesized. The eval logs preserve message *order* and
  content but not per-message wall-clock time; `created_at` uses the source
  repo's `lastModified` and each `dialog.start` is a monotonic offset. See
  `docs/mapping.md`.
- **Truncated JSON**: a few tool-call arguments / results are truncated in the
  source logs. The parser preserves the raw string (`_raw_arguments` /
  `_raw_result`) rather than dropping the turn; the vCon stays schema-valid.
- **UUIDs** are deterministic (derived from the source identity) so re-running
  yields stable, diff-friendly output; version bits mark them UUIDv8 as the
  draft recommends.
- This targets the **core** container only. The adopted WG extensions
  (contact-center, privacy-primer) are noted in the spec notes but not exercised.
