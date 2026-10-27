# vcon-trajectories

**Do real agent trajectories — in the vendors' own formats — fit the IETF vCon
`ai_agent` extension?** This repo is the test bench for
[`draft-birkholz-vcon-ai-agent-extension`](https://github.com/henkbirkholz/draft-birkholz-vcon-ai-agent-extension):
it parses native Claude Code (Anthropic), Codex CLI (OpenAI) and Gemini CLI (Google)
sessions into one neutral trajectory model, emits `ai_agent` vCons, validates them
against the draft's own CDDL, and reports where the draft fits and where it doesn't.

> **Draft:** [henkbirkholz/draft-birkholz-vcon-ai-agent-extension](https://github.com/henkbirkholz/draft-birkholz-vcon-ai-agent-extension) · pinned copy in [`schema/ai-agent/`](schema/ai-agent/) · findings for the authors in [`docs/draft-feedback.md`](docs/draft-feedback.md)

```
81 real sessions / 4 corpora → 81/81 valid against the draft CDDL (+ semantic checks)
draft's own examples: 2/2 accepted, 12/12 negative controls rejected
```

Pinned to draft commit [`35c126d`](schema/ai-agent/PINNED.md) (vCon core syntax 0.5.0 —
adds the `sessions[]` and `events[]` arrays this design relies on).

## Framing: trajectories as the vendors define them

A trajectory is the ordered record of one agent run: the human prompt, the model's
reasoning, each tool call and its result, the final answer, plus run metadata (model,
harness version, working directory, repo state, token usage). Each vendor's harness
logs this natively; the draft's job is to be a common, verifiable container for all of them.

| Concept | Anthropic (Claude Code / Messages API) | OpenAI (Codex CLI / Responses API) | Google (Gemini CLI) | `ai_agent` vCon |
|---|---|---|---|---|
| message | `user`/`assistant` record, `text` block | `response_item` `message` | `user_prompt` / `assistant_response` | `dialog[]` `text` |
| reasoning | `thinking` / `redacted_thinking` block | `reasoning` item (`summary`, `encrypted_content`) | — (not in logs) | `events[]` `reasoning` (`content`, `encrypted`) |
| tool call | `tool_use` block (`id`, `name`, `input`) | `function_call` (`call_id`, `arguments`) | `tool_use` (`run_shell_command`, `replace`, …) | `events[]` `tool-call` (`call_id`, `tool_name`, `input`) |
| tool result | `tool_result` block (`is_error`) | `function_call_output` + `exec_command_end` exit code | — (not in logs) | `events[]` `tool-result` (`call_id`, `is_error`, `status`) |
| tree structure | `uuid` / `parentUuid` | — | — | `entry_id` / `parent_id` |
| sub-agent | `isSidechain`, `Task` tool | — | — | child `Session` via Session_Reference |
| token usage | `message.usage` | `token_count` event | per-turn counts | `Dialog.token_usage` (or `system-event`, see feedback) |
| harness / model | `message.model`, `version` | `turn_context.model`, `cli_version` | model, CLI name | `Party.agent_meta` |
| run context | `cwd`, `gitBranch` | `cwd`, `git` | repo | `Session.environment`, `vcs` |

Details: [`docs/vendor-trajectories.md`](docs/vendor-trajectories.md).

## Datasets — and an honest caveat

**None of the three vendors publishes an official trajectory dataset** (searched
2026-10-26). What exists are third-party captures of the vendors' own harnesses, which
is what native-format validation needs:

| Vendor harness | Corpus | Sessions swept | Notes |
|---|---|--:|---|
| Claude Code | [trace-commons/agent-traces](https://huggingface.co/datasets/trace-commons/agent-traces) (CC-BY-4.0) | 27 | raw session JSONL |
| Claude Code | [SALT-NLP/SWE-chat](https://huggingface.co/datasets/SALT-NLP/SWE-chat) (ODC-By; ungated mirror `cfahlgren1/SWE-chat`) | 25 | real developers, raw JSONL |
| Codex CLI | SWE-chat | 25 | raw rollout JSONL |
| Gemini CLI | SWE-chat | 4 | **normalized turn rows, not raw logs; no tool results**. A raw Gemini CLI / ADK parser is not done — no public raw corpus found |

Also exercised through small adapters (`src/vcon_trajectories/sources/`): tau-bench,
SWE-rebench/OpenHands, Hermes, Mind2Web (GUI), API-Bank, OpenInference spans.
Attribution and licenses: [`examples/ATTRIBUTION.md`](examples/ATTRIBUTION.md).

## Results

- Full sweep: [`docs/corpus-report.md`](docs/corpus-report.md) — validity, which draft constructs
  real data exercises, native records that have no mapping.
- What the data says about the draft: [`docs/draft-feedback.md`](docs/draft-feedback.md) (gaps,
  with evidence and suggested changes). Headlines: `token_usage` has no home on events and its `input` semantics differ by vendor;
  no cross-array ordering; `Session_Reference` can't name the spawning call; `file_attribution` needs a pinned hash canonicalization.
- Beyond the draft: [`docs/formats.md`](docs/formats.md) / [`docs/fidelity.md`](docs/fidelity.md) — export to
  ATIF (Harbor) and OpenTelemetry GenAI spans, ATIF import, and a round trip over 178 real Harbor
  trajectories (all valid, no steps / tool calls / prompt tokens lost).
- `file_attribution` is now derived from real edit diffs and checked against SWE-chat's labels
  ([`docs/attribution-check.md`](docs/attribution-check.md)); real sub-agent results produce child Sessions
  (`examples/anthropic/claude-code-subagent.vcon.json`). Findings: `docs/draft-feedback.md` §9. Not yet
  exercised by real data: per-range contributors across models, and a child Session with its own transcript.

## Layout

```
schema/ai-agent/   pinned draft CDDL, draft source, draft's examples + negative controls
src/vcon_trajectories/
  ir.py            vendor-neutral Turn / UTrajectory
  native/          claude_code.py · codex.py · gemini_cli.py · atif.py   (native parsers; ATIF = Harbor)
  sources/         adapters for non-vendor corpora (benchmarks, telemetry)
  ai_agent.py      IR -> ai_agent vCon (the one place the mapping lives)
  export/          ai_agent vCon -> ATIF (atif.py) · OTel GenAI spans (otel_genai.py) + their checkers
  validate.py      compose draft CDDL + run Ruby `cddl` gem + semantic checks
  attribution.py   replay recorded file edits -> the draft's file_attribution
  coverage.py      which draft constructs a vCon exercises
examples/          one real, capped, redacted vCon per corpus
scripts/           build.py (examples + --report sweep) · validate.py · fidelity.py · attribution_check.py · corpora.py (fetchers)
```

## Run

```bash
gem install cddl                       # Ruby reference CDDL validator
python -m venv .venv && .venv/bin/pip install pytest pyarrow
.venv/bin/python -m pytest             # offline tests (synthetic records + draft controls)
.venv/bin/python scripts/validate.py   # draft controls + committed examples
.venv/bin/python scripts/build.py --report   # re-fetch corpora, rebuild examples + docs/corpus-report.md
```

`build.py --report` downloads public data into `.cache/` (the Gemini extract scans a 1.3 GB parquet once).

## Status of the draft

An individual Internet-Draft by the vCon working group authors, not an adopted standard; it
changes often. This repo tracks a pinned commit — bump `schema/ai-agent/PINNED.md` and rerun
to follow it.
