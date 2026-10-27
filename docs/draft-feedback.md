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

## What worked well
Event typing (`tool-call`/`tool-result`/`reasoning`), `call_id` pairing, `entry_id`/`parent_id`
for Claude's tree, `reasoning.encrypted` + empty `content` for Codex, `agent_meta`
+ `environment` + `vcs` for run context, and the strict CDDL with negative controls
(together with the semantic checks it caught real converter bugs here: orphan tool-results from `think` calls, and token counts that were silently dropped).
