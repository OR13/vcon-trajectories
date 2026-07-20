# Mapping conventions — what is standard vs. what is our interpretation

This project maps agent-trajectory concepts onto the vCon container. Some of those
mappings are **directly supported by the spec**; others **reuse standard vCon
constructs in ways the spec does not define** for agent trajectories. This page
draws that line explicitly so nothing here is mistaken for an IETF-endorsed
mapping.

> **Authority:** the vCon container is defined by `draft-ietf-vcon-vcon-core`.
> Only that document (and other adopted vCon WG drafts) defines what a vCon
> construct *means*. Where this project applies a construct to something the spec
> doesn't describe, that is **our convention**, not a standard.

## Legend
- **Standard** — the construct and this use of it are described by the spec.
- **Convention** — the construct is standard, but *applying it to this agent
  concept* is this project's interpretation, **not** defined or endorsed by the
  IETF vCon working group.

## Core mappings (Standard)

These use vCon constructs for the kind of thing they were defined for; only the
*content domain* (agent trajectories) is new, which is expected of any vCon
producer.

| Agent concept | vCon construct | Status |
|---|---|---|
| user / model / tool as participants | `parties[]` (`type` person/bot) | Standard |
| a message / tool call / tool result / turn | `dialog[]` (`type:"text"`) | Standard |
| model reasoning / eval metadata / reward | `analysis[]` (`type:"report"`) | Standard |
| system prompt / tool definitions | `attachments[]` | Standard |
| large content by reference | `url` + `content_hash` (SHA-512, SRI form) | Standard |
| binary/multimodal content inline | `encoding:"base64url"` | Standard |
| structured tool payloads | `encoding:"json"` | Standard |

The `analysis` `schema` values we use (`chain-of-thought`, `trajectory-metadata`,
`qwythos-eval`, `mythos-agent-metadata`, `mapping-note`) are free-form labels we
chose; `schema` is a free string in the spec, so this is standard usage, but the
label vocabulary is ours.

## Reuses (Convention — NOT standard for agent trajectories)

Demonstrated under [`examples/conventions/`](../examples/conventions/). Each of
those vCons also embeds this disclaimer as a `mapping-note` analysis entry.

| Agent concept | vCon construct reused | Why it's a convention |
|---|---|---|
| **agent → agent handoff / delegation** | `dialog.type:"transfer"` (`transferor`, `transfer_target`, `transferee`) | vCon `transfer` is defined for **telephony call transfer**. We set `transferor` = delegating agent, `transfer_target` = receiving agent, `transferee` = the user/task party (an approximation). The spec does not define `transfer` for multi-agent handoff. |
| **aborted / failed run leg** | `dialog.type:"incomplete"` + `disposition` | vCon `incomplete`/`disposition` are defined for **telephony calls that did not connect**; the enum is `no-answer / congestion / failed / busy / hung-up / voicemail-no-message`. Only `"failed"` reasonably fits an aborted agent run. Reusing it for agent trajectories is our convention. |

### Honesty caveats in the demonstrators
- `multi-agent-transfer.vcon.json` uses **real** data (`Kevin355/Who_and_When`,
  Magentic-One). The `transfer` field assignment is an approximation (see above).
- `incomplete-run.vcon.json` is **synthetic**, authored only to show the construct.
- `external-and-binary-content.vcon.json` uses **standard** `url`+`content_hash`
  and `base64url`, but the `url` is **illustrative** (it does not dereference to
  the hashed bytes; the `content_hash` is a real SHA-512 of the included DOM) and
  the PNG is a 1×1 placeholder.

## If you want a *standard* agent-trajectory mapping

The IETF vCon group has draft work aimed exactly at this — `agent_session` /
Verifiable Agent Conversations (see [`docs/trajectory-sources.md`](trajectory-sources.md)).
Targeting that extension (rather than these core-construct reuses) is the path to
a mapping with actual standards backing; this repo currently maps to **core only**
and treats the two reuses above as clearly-labeled conventions.
