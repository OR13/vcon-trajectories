# Other trajectory formats

The draft is one of several attempts to standardize "what an agent did". This repo converts
`ai_agent` vCons to, and reads from, the ones that have a public spec and real data.

| Format | Spec (vendored, pinned) | Direction | Real data checked | Status |
|---|---|---|---|---|
| **ATIF** (Harbor, v1.8) | `schema/atif/` | vCon -> ATIF, ATIF -> vCon | 178 Terminal-Bench 2.0 trajectories (Apache-2.0) | done |
| **OpenTelemetry GenAI** (Development) | `schema/otel-genai/` | vCon -> spans | the 10 committed examples | export only; checked against the spec text |
| **OpenInference** (Arize) | n/a (not vendored) | span adapter only (`sources/adapters.py`) | Phoenix sample | partial, not aligned to OTel GenAI attrs |
| **Inspect AI** logs (UK AISI) | not vendored | none | none | not started |

## What "validated" means here

- **ATIF**: `export/atif_check.py` re-implements the RFC's stated rules (sequential `step_id`, source values,
  agent-only fields, `tool_call_id` / `source_call_id` pairing, subagent refs, `cached_tokens <= prompt_tokens`).
  It accepts all 178 real Harbor trajectories, which is evidence the rules are not stricter than Harbor's own
  output, **not** a conformance certificate. Harbor's own validator was not run (installing the package was
  not done in this session).
- **OTel**: `export/otel_check.py` checks span-tree integrity, the Required attributes, the
  "input tokens include cached" rule, and the shape of `gen_ai.output.messages` parts. The spec's own pydantic
  models are vendored but not executed. The conventions are in *Development* status and may change.
- **Round trips** (`scripts/fidelity.py`, `docs/fidelity.md`) measure counts of messages / tool calls / results /
  reasoning, token sums, call-result pairing and error flags, via this repo's own importer. They show nothing is
  silently dropped; they are a self-consistency check, not independent proof, except for the real-ATIF block,
  where the input was produced by someone else's exporter.

## Mapping decisions

| vCon `ai_agent` | ATIF | OTel GenAI |
|---|---|---|
| user Dialog | `step(source=user)` | (input message; not reconstructed) |
| assistant Dialog + reasoning + tool-calls of one turn | one `step(source=agent)` | one `chat` span, `gen_ai.output.messages` |
| `tool-call` / `tool-result` | `tool_calls[]` / `observation.results[]` (by `call_id`) | `execute_tool` span (`gen_ai.tool.call.*`) |
| `is_error`, `status` on tool-result | `results[].extra` (ATIF has no field) | span status ERROR + `error.type` |
| `token_usage`, `token-count` events | `metrics` (`prompt_tokens` inclusive, `cached_tokens`; rest in `extra`) | `gen_ai.usage.*` (`cache_read` / `cache_write`) |
| `reasoning` (+ `encrypted`) | `reasoning_content`; blocks in `extra.vcon_reasoning` | `reasoning` part |
| other `system-event` | `step(source=system)` with `extra.event_type` | not exported |
| child Session | `subagent_trajectories[]` + `subagent_trajectory_ref` | child `invoke_agent` under the spawning `execute_tool` |
| `agent_meta`, `environment`, `vcs` | `agent`, `extra` | `gen_ai.agent.*`, `gen_ai.provider.name`, `gen_ai.request.model` |

Not carried: `entry_id` / `parent_id` (the native tree) and `file_attribution` have no ATIF or OTel field.

`token_usage.input` is read as including cached tokens (see `draft-feedback.md` §8); the Claude Code parser
normalizes Anthropic's exclusive `input_tokens` to that convention.
