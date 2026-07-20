# Extracted spec + draft status (as prototyped)

> Built against the drafts as fetched **2026-07-20**. Both are **individual
> Internet-Drafts at revision `-00`, NOT adopted vCon working-group documents**,
> with the standard "no formal standing in the IETF standards process"
> boilerplate. They may change or expire. Nothing here is a standard.

| Draft | Rev | Date | Standing | Intended status |
|---|---|---|---|---|
| `draft-howe-vcon-agent-session` | -00 | 2026-05-20 (exp 2026-11-21) | individual, not WG-adopted | Standards Track (aspirational for an unadopted draft) |
| `draft-birkholz-verifiable-agent-conversations` (VAC) | -00 | 2026-02-25 (exp 2026-08-29) | individual, not WG-adopted | none assigned |

Sources: datatracker + the drafts' GitHub repos (`vcon-dev/draft-howe-vcon-agent-session`,
`xor-sciences/draft-birkholz-verifiable-agent-conversations`). The VAC CDDL is
vendored here as [`agent-conversation.cddl`](agent-conversation.cddl) (verbatim
copy of the draft's include file, for validation).

## `agent_session` extension (draft-howe-vcon-agent-session-00)

A "Compatible" extension — **no new top-level keys**; it uses:

- **Declaration:** `"agent_session"` in the vCon `extensions` array (and in
  `critical` if consumers MUST process the trace).
- **Agent party:** a `parties[]` entry with `"role":"agent"`,
  `"validation":"system"`, `"name"`, and
  `"meta":{"agent_session":{ "model_id"(req), "provider"(req),
  "recording_agent"(rec), "environment"{cwd,vcs_branch,vcs_commit}(opt) }}`.
  (vCon keys use **underscores**.)
- **Dialog:** user prompts / assistant replies are ordinary `dialog[]` text
  entries — no new dialog type.
- **Trace:** ONE `analysis[]` entry with `"type":"agent_trace"` (MUST),
  `"dialog"` indices, `"vendor"`=provider, `"product"`=model_id,
  `"schema"`=VAC URL, `"encoding"`=`"json"` (or `"base64url"` for CBOR), and
  `"body"` = the VAC record.
- **Attachment `purpose` values:** `agent_file_change`, `agent_artifact`,
  `agent_environment`, `scitt_receipt`, `agent_trace_cose_sign1`.

## VAC record (draft-birkholz-verifiable-agent-conversations-00)

`verifiable-agent-record` (unsigned) — required `version`, `id`, `session`;
optional `created`, `file-attribution`, `vcs`, `recording-agent`. The
`session` (`session-trace`) has `session-id`, `agent-meta`
(`model-id`,`model-provider` required), optional `environment`
(`working-dir`,`vcs`), and an ordered `entries: [* entry]`. **VAC keys use
hyphens.** Entry `type` discriminator:

| entry `type` | key fields |
|---|---|
| `user` / `assistant` | `content`, `model-id` (assistant), `timestamp`, `token-usage` |
| `tool-call` | `name`, `input`, `call-id` |
| `tool-result` | `output`, `call-id`, `status`, `is-error` |
| `reasoning` | `content`, `encrypted?` |
| `system-event` | `event-type`, `data` |

Signed form `signed-agent-record` = COSE_Sign1 (`#6.18`), SCITT-interoperable,
payload = serialized record (or detached w/ `trace-metadata.content-hash`).
Authors: Henk Birkholz, Tobias Heldt, Orie Steele.

## This prototype's IR → VAC/agent_session mapping choices

| IR turn | VAC entry | Note |
|---|---|---|
| MESSAGE (user/assistant) | `user` / `assistant` | assistant carries `model-id` |
| REASONING | `reasoning` | |
| TOOL_CALL / ACTION | `tool-call` | `call-id` from IR `meta.id` |
| TOOL_RESULT | `tool-result` | `is-error`/`status:"error"` when errored |
| OBSERVATION | `tool-result` (no `call-id`) | **our choice** — VAC has no observation type |
| HANDOFF | `system-event` `event-type:"agent-handoff"` | **our choice** — VAC has no handoff type |
| INCOMPLETE | `system-event` `event-type:"run-incomplete"` | **our choice** |

**Omissions/assumptions (honest):**
- Emits the **unsigned** `verifiable-agent-record`; `signed-agent-record`
  (COSE_Sign1/CBOR) is **not** produced.
- `model-id`/`provider` are supplied per source from what the data actually
  states (Claude Code session model + `anthropic`; tau-bench `gpt-4o`+`openai`);
  where unknown they would be `"unknown"`.
- OBSERVATION/HANDOFF/INCOMPLETE mappings above are ours, not spec-defined.

## Validation performed

- Outer `agent_session` vCons: valid against the **core** vCon JSON Schema **and**
  `schema/vcon.cddl` (they are valid core vCons plus permitted extension fields).
- Embedded VAC records: valid against the **VAC draft's own**
  `agent-conversation.cddl` (Ruby `cddl` gem).
