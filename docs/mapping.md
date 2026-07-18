# Mapping: Mythos agent trajectories → IETF vCon (v0.4.0)

Target: `draft-ietf-vcon-vcon-core-03`, container version `0.4.0`. Output is
validated against the draft's Appendix B JSON Schema (`schema/vcon_json_schema.json`).

## Source data

The trajectories come from the **public** eval logs of the Mythos model repo
`empero-ai/Qwythos-9B-Claude-Mythos-5-1M` (see `docs/data-source.md`):

- `evals/tool_test_outputs.md` — multi-round **agentic tool-use** trajectories
  (thinking → `tool_call` → tool `Result` → … → final answer).
- `evals/sample_generations.md` — single-turn generations with a separate
  reasoning (chain-of-thought) trace and an answer.

One trajectory (one test case / one prompt) → **one vCon**.

## Party model

| Index | Role in trajectory | vCon Party |
|-------|--------------------|------------|
| 0 | the human prompt | `{type:"person", name:"user"}` |
| 1 | the model under test | `{type:"bot", name:<model>, org:"empero-ai"}` |
| 2..n | each distinct tool/environment | `{type:"bot", name:<tool>, org:"empero-ai"}` |

Tools are modeled as bot parties so that a `tool_result` dialog has a real
`originator` (the tool that produced it), preserving who-said-what.

## Dialog model

Every trajectory event becomes one `dialog` entry of `type:"text"` in temporal
order. `start` is synthesized (the eval logs are not per-message timestamped —
see "Timestamps"). `parties` lists the involved party indices; `originator` is
the speaker.

| Event | `type` | `originator` | `body` / `encoding` |
|-------|--------|--------------|---------------------|
| user prompt | text | 0 (user) | prompt string / `none` |
| assistant reasoning+message | text | 1 (model) | visible assistant text / `none` |
| tool call | text | 1 (model) | `{"tool":name,"input":{...}}` / `json` |
| tool result | text | tool party | result object / `json` |
| final answer | text | 1 (model) | answer string / `none` |

`application` on tool-call/result dialogs carries the tool name.
`mediatype` is `text/plain` for `none` bodies, `application/json` for `json` bodies.

## Analysis model

Model-internal reasoning (chain-of-thought) and trajectory-level eval metadata
are captured as `analysis` entries (they are *about* the dialog, not dialog
themselves):

- **Reasoning trace** → `{type:"report", vendor:"empero-ai", product:<model>,
  schema:"chain-of-thought", dialog:[<assistant dialog idx>], body:<reasoning>,
  encoding:"none"}`.
- **Trajectory metadata** → `{type:"report", vendor:"empero-ai", product:<model>,
  schema:"qwythos-eval", dialog:[…all dialog idxs…], body:{test_id, rounds,
  duration_s, tools_used, category}, encoding:"json"}`.

`type:"report"` is used because the draft's analysis `type` values
(report/sentiment/summary/transcript/translation/tts) have no "reasoning" member;
`report` is the general-purpose bucket and `schema` names the concrete format.

## Attachments

For tool-use trajectories, the set of tool definitions available to the agent is
attached: `{purpose:"tool-definitions", party:1, dialog:0, mediatype:
"application/json", body:[{name,...}], encoding:"json", start:<base>}`.
(Attachments require `start`, `party`, `dialog` per the schema.)

## Top-level fields

| vCon field | Value |
|------------|-------|
| `vcon` | `"0.4.0"` |
| `uuid` | deterministic UUIDv8 derived from `repo + file + test_id` (reproducible) |
| `created_at` | source repo `lastModified` (`2026-07-14T12:41:41Z`) |
| `subject` | test name, or `"[<category>] <prompt excerpt>"` |
| `parties`, `dialog`, `analysis`, `attachments` | as above |

## Timestamps

The eval logs contain only a per-test total duration (tool tests) and no
per-message time. `created_at` uses the source repo's `lastModified`. Each
dialog `start` = `created_at + (index seconds)`, i.e. synthesized monotonic
ordering. This is documented rather than hidden: the vCons faithfully preserve
message **order** and content; absolute wall-clock times are not recoverable
from the source and are approximated.
