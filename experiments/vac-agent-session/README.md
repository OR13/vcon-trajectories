# Experiment: mapping to `agent_session` / VAC (kept separate from core)

> **This is an experimental prototype, deliberately walled off from the rest of
> the repo.** Everything under `experiments/` targets the IETF **`agent_session`
> vCon extension** (`draft-howe-vcon-agent-session`) and **Verifiable Agent
> Conversations** (`draft-birkholz-verifiable-agent-conversations`, "VAC").
>
> The main repo maps trajectories to **vCon 0.4.0 core** and makes no claim about
> these extensions. Nothing here changes or depends on the core mapping.

## Status & honesty

- `draft-howe-vcon-agent-session` and `draft-birkholz-verifiable-agent-conversations`
  are (as of this writing) **individual Internet-Drafts, not adopted vCon working
  group documents**. They can change or expire at any time. Treat this prototype
  as tracking a moving target, not implementing a standard.
- Where this prototype has to fill a gap the drafts leave ambiguous, that choice
  is **ours** and is labeled as such — not implied to be spec-defined.
- Draft status/versions this prototype was built against are recorded in
  [`SPEC.md`](SPEC.md) with the exact revision numbers and fetch date.

## Why separate

The core mapping is stable, validated (JSON Schema + CDDL), and standards-anchored
to an adopted WG draft. The extension work is early and speculative. Keeping them
apart means the core deliverable isn't muddied by experimental, possibly-wrong
interpretations of unadopted drafts.

## Contents

- [`SPEC.md`](SPEC.md) — extracted `agent_session` + VAC data model + exact draft
  status/versions (both `-00`, individual, not WG-adopted).
- [`agent-conversation.cddl`](agent-conversation.cddl) — verbatim copy of the VAC
  draft's CDDL include (for validation).
- [`vac.py`](vac.py) — converter: the core project's shared IR
  (`vcon_trajectories.sources.ir`) → a VAC `verifiable-agent-record` and an
  `agent_session`-extended vCon.
- [`build_examples.py`](build_examples.py) — builds `examples/` from two real
  sources (a Claude Code session; tau-bench).
- [`examples/`](examples/) — per source: `*.vcon.json` (agent_session vCon whose
  `analysis[0].body` is the VAC record) and `*.vac.json` (the record alone).
- [`test_vac.py`](test_vac.py) — validation, run separately from the core suite.

## What validates (run `python build_examples.py`, then the checks below)

- **Outer `agent_session` vCons** → valid against the **core** vCon JSON Schema
  **and** `schema/vcon.cddl`. They are ordinary core vCons plus the extension's
  permitted fields (agent party `role`/`meta.agent_session`, `analysis.type:
  "agent_trace"`, `extensions:["agent_session"]`).
- **Embedded VAC records** → valid against the **VAC draft's own**
  `agent-conversation.cddl` (Ruby `cddl` gem):
  ```bash
  cddl experiments/vac-agent-session/agent-conversation.cddl validate \
       experiments/vac-agent-session/examples/agent-session-taubench.vac.json
  ```

## Attribution

Example inputs derive from `trace-commons/agent-traces` (CC-BY-4.0) and
`sierra-research/tau-bench` (MIT); `agent-conversation.cddl` is copied verbatim
from `xor-sciences/draft-birkholz-verifiable-agent-conversations`. Regenerate:
`python experiments/vac-agent-session/build_examples.py`.

## Not implemented (honest)

- The **signed** form (`signed-agent-record` / COSE_Sign1, CBOR) is not produced —
  only the unsigned `verifiable-agent-record`.
- `attachments[]` extension purposes (`agent_file_change`, `scitt_receipt`, …)
  and file-attribution are not exercised.
- OBSERVATION / HANDOFF / INCOMPLETE → VAC entry choices are ours (see SPEC.md),
  not spec-defined.
