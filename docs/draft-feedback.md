# Feedback on draft-birkholz-vcon-ai-agent-extension

Evidence from converting real Claude Code / Codex CLI / Gemini CLI sessions
(`corpus-report.md`, pinned draft `35c126d`). The draft fits the data: **81/81 real
sessions validate**, every native message/tool/reasoning shape found a home. These are
the places where it was awkward or silent. Ordered by how much real data they touch.

## 1. `token_usage` only exists on Dialog
Claude Code logs usage on every API response, but most responses are `thinking` and
`tool_use` only (no text message). In the Claude sweep **2,385 of 11,778 events (20%) in
agent-traces and 6,858 of 36,738 (19%) in SWE-chat** are `token-count` system-events created
only because usage had nowhere else to go; Codex natively emits `token_count` events too.
*Suggest:* define `token_usage` on the four event types (an event-ext) or a `token-usage`
Event type, and say which entry a usage record belongs to.

## 2. `child` sessions can't be tied to the call that spawned them
Sub-agent spawns are common in real data (the Claude `Task`/`Agent` tool appears in 30 of 52
Claude sessions) but sub-agent transcripts live in separate files, so **no real session
produced a child Session** — that path is only covered by a synthetic test. Also,
Session_Reference has no way to name the spawning `tool-call` (`call_id`).
*Suggest:* a `call_id`/`entry_id` link on Session_Reference (or `spawned_by`), and a real example.

## 3. No total order across `dialog[]` and `events[]`
Messages and events are separate arrays. Merging needs `time`, but ties are routine
(Codex parallel tool calls share the same millisecond; some sessions start several events
at the same instant). `parent_id` would disambiguate but Codex has no entry ids.
*Suggest:* an optional monotone `seq`, or state that array order within `events[]` is
authoritative and how dialog interleaves.

## 4. `parent_id` when native entries are not recorded
Claude's `parentUuid` frequently points at records a recorder drops (hook attachments,
file snapshots). Verbatim copying leaves dangling `parent_id`s; this repo re-links to the
nearest recorded ancestor. *Suggest:* the draft should say which (and whether a recorder
must preserve the original id elsewhere).

## 5. `system-event.event_type` needs a vocabulary
Observed (all vendor-specific): `token-count`, `task-started`, `task-complete`,
`turn-aborted`, `developer-instructions`, `context-injection`, `compact_boundary`,
`turn_duration`, `api_error`, `stop_hook_summary`, `local_command`, `bridge_status`
(full counts in the report). Several carry meaning an auditor wants (context compaction
changes what the model saw; `api_error`, `turn-aborted` are failures).
*Suggest:* an IANA-registered core set (token-count, compaction, error, abort, context-injection).

## 6. Things real logs carry that have no construct
| Native | Seen in | Count (swept) |
|---|---|--:|
| images in user messages | Claude | 27 |
| hook / attachment records | Claude | 1,587 |
| `patch_apply_end` (file changes) | Codex | 590 |
| MCP tool-call end, web-search end | Codex | 85 |
| context compaction (`compacted`) | Codex | 27 |
| PR links | Claude | 73 |

`patch_apply_end` and Claude's file-history snapshots are the natural source for
`file_attribution`, which the draft marks unvalidated — **not attempted here**; SWE-chat
also ships human-vs-agent line attribution (`sessions.agent_lines`, `commits`) that could
validate it. This is the best next experiment.

## 7. Smaller points
- Claude `thinking` blocks often arrive with empty text and only a `signature` (1,022 in the sweep, vs. the reasoning events with text). The signature is a replay-integrity token, not ciphertext, so it doesn't fit `reasoning.encrypted`; this repo emits an empty-`content` reasoning event and drops the signature. The draft could say how (or whether) such tokens are recorded.
- `tool-result` requires `party` = the agent; tools/environments are not parties. Fine, but worth one sentence (GUI observations become tool-results the same way).
- Tool definitions are not in any native session log (only in some dataset wrappers); this repo carries them as `attachments[]` where available — the draft is silent.
- Agent handoff between peer agents (Who&When/Magentic-One) has no construct; this repo's adapter emits a vendor `agent-handoff` system-event. Not validated here beyond the adapter.

## 8. Findings from mapping to ATIF and OpenTelemetry GenAI

Round-tripping through the two most visible trajectory formats (see [`formats.md`](formats.md)) turned up
points the vendor-native logs alone did not:

- **`token_usage.input` has no stated semantics.** Claude's API reports `input_tokens` *excluding* cache reads
  and writes; OpenAI/Codex, ATIF (`prompt_tokens`) and OTel (`gen_ai.usage.input_tokens`) define input as
  *including* cached tokens. The draft says only that `cached` is "input tokens served from cache". Un-normalized,
  the same field means different things per vendor (Claude `input: 3, cached: 26743` vs Codex `input: 27000,
  cached: 26743`). This repo now normalizes to the inclusive convention; the draft should state it.
- **No field for cache-write tokens.** Anthropic bills `cache_creation_input_tokens` separately and OTel has
  `gen_ai.usage.cache_write.input_tokens`; `token_usage` has no member for it (this repo uses the open `* tstr => any`
  to carry `cache_write`). Suggest naming it.
- **ATIF and OTel have a place for per-call usage next to the call; the vCon does not** (see §1). Both folded
  usage into the agent step / `chat` span; the vCon needed a `token-count` event workaround for ~20% of events.
- **Subagent linkage.** ATIF puts the reference *on the tool result that returned the sub-agent's output*
  (`subagent_trajectory_ref`); OTel parents the child `invoke_agent` span under the spawning `execute_tool` span.
  Both tie the child to a specific call. `Session_Reference` cannot (see §2), so the exporters match children to
  `Task`/`Agent` calls by order, which is a heuristic.
- **Out-of-band child trajectories.** Harbor's `terminus-2` records context summarization as three sub-trajectories
  stored in *separate files* (`trajectory_path`), not embedded. A vCon `Session_Reference` has no way to point at a
  session that is not in the same vCon; this repo keeps the refs as a `subagent-delegation` system-event.
- **No tool-error flag in ATIF, `is_error`/`status` in the vCon.** The vCon is richer here; OTel has `error.type`
  and span status. Worth keeping.
- **Ordering again (§3).** Producing steps/spans required inventing a total order across `dialog[]` and `events[]`:
  (time, think < say < act < observe, array position). Any consumer has to do the same.
- **`reasoning` with no content and no `encrypted`** (signature-only Claude blocks) is representable but carries
  nothing; ATIF has no field for it either, so it survives export only as an empty block in `extra`.

## 9. `file_attribution` and child sessions, exercised on real data

`file_attribution` is derived (`src/vcon_trajectories/attribution.py`) by replaying the line-numbered diffs
harnesses record: Claude Code `Edit`/`Write` results (`structuredPatch`, `create` content) and Codex
`patch_apply_end` unified diffs. Over 52 real sessions (27 Claude Code from agent-traces, 25 Codex from SWE-chat): 33 had replayable edits (25/27 Claude, 8/25 Codex), 763
files and 74,575 lines attributed, 100% of vCons valid against the draft CDDL. Checked against SWE-chat's own
labels on 80 Codex sessions (`docs/attribution-check.md`): median file recall 0.76, precision 0.36 (agents edit
files that are never committed), line ratio 1.15 against `agent_lines`. What the data says about the draft:

- **It works, with `content_hash` as the key.** Line numbers shift with every later edit, so ranges are only
  correct if edits are replayed in order; the hash is what lets a consumer re-find them. The draft does not define
  what is hashed. This repo hashes the range's lines joined with `\n` (CRLF normalized, no trailing newline); the
  draft should pin a canonicalization, since Windows sessions in the corpus have CRLF files.
- **Only `ai` ranges are derivable from a session log.** `human` / `mixed` need the commit history (SWE-chat gets
  them from git). The ranges are therefore a lower bound on AI authorship of a file, not a partition; worth saying.
- **Positions are "as of the last edit in the session", not as committed.** Suggest a way to say which revision the
  line numbers refer to (a `vcs.revision` is available, but nothing ties ranges to it).
- **No link from a File_Conversation to a Session.** In a vCon with child sessions there is no way to say which
  session wrote a range (only an optional `url`). Suggest `session: uint`.
- **Paths are absolute in every native log, including Windows paths (`d:\CFML\...`).** Making them repo-relative
  needs the working directory; 54 files across 52 sessions were outside it and cannot be represented.
- **Shell edits are invisible.** `sed -i`, redirects and formatters change files without a diff in the log; this is
  most of the 24% of SWE-chat files we miss. Recorders that can observe the file system should say so.
- **Per-range `contributor` (mixed models) is unexercised by real data:** no session in the sample switched models
  mid-file. It is covered by unit tests only.

Child sessions, from real data (7 sessions with a `Task` sub-agent result; example
`examples/anthropic/claude-code-subagent.vcon.json`): the parent log holds the sub-agent's *summary* (id, type,
prompt, duration, total tokens, tool counts) but not its transcript, so the child Session has no dialog. That is a
legitimate, common case. Observations:

- A child Session needs somewhere to put run-level facts: duration is derivable from `start`+`duration`, but
  tokens and tool counts (`totalTokens`, `totalToolUseCount`) have no Session-level home. This repo emits
  `subagent-start` / `subagent-end` system-events (start time derived as end minus `totalDurationMs`, flagged).
- `Session_Reference` still cannot name the spawning call; this repo writes `(call <id>)` into `description`.
- Whether a Session may legitimately be empty is not stated; the CDDL accepts it.

## What worked well
Event typing (`tool-call`/`tool-result`/`reasoning`), `call_id` pairing, `entry_id`/`parent_id`
for Claude's tree, `reasoning.encrypted` + empty `content` for Codex, `agent_meta`
+ `environment` + `vcs` for run context, and the strict CDDL with negative controls
(together with the semantic checks it caught real converter bugs here: orphan tool-results from `think` calls, and token counts that were silently dropped).
