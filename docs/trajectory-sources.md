# Candidate trajectory sources + coverage matrix

Verified catalog of **real, public JSON agent-trajectory sources** and how they
cover the [trajectory feature space](trajectory-feature-space.md). Goal: pick the
**minimum set whose union exercises every feature** the vCon mapping must handle.

All access/license/schema facts below were verified against live HF/GitHub pages
(2026-07). "Genuine trajectory" = assistant calls tool → tool result → assistant
continues (not single-shot function-call pairs).

## ⭐ Most important finding: the IETF already defined the destination

There is active 2026 IETF work mapping agent traces → vCon:

- **`draft-howe-vcon-agent-session`** — an `agent_session` vCon extension: each
  agent → `parties[]` (`role:"agent"` + `meta.agent_session`: model_id, provider,
  commit); prompts/replies → `dialog[]`; the internal trace → **one `analysis[]`
  entry `type:"agent_trace"`** whose body is a **VAC** record; modified files →
  `attachments[]`. (github.com/vcon-dev/draft-howe-vcon-agent-session)
- **`draft-birkholz-verifiable-agent-conversations` (VAC)** — the CDDL-defined,
  COSE-signable trace payload embedded by agent-session.
- **`draft-howe-vcon-mcp-session` + `vcon-mcp-proxy`** — a running pipeline that
  intercepts MCP JSON-RPC and emits vCon 0.4.0 (parties=client/server,
  dialog=JSON-RPC payloads+timestamps, analysis=tool-call counts).

**Unclaimed gap:** nothing published converts the existing HF/GitHub trajectory
corpora (SWE-agent, OpenHands, tau-bench, OpenInference exports, …) into vCon
`agent_session`/VAC records. That transform is essentially this project.
→ **Decision point:** align our output to the `agent_session`/VAC shape, or keep
the current core-only mapping. (See README follow-ups.)

## Status: all 7 wired up ✅

All seven public sources below now have working adapters
(`src/vcon_trajectories/sources/adapters.py`) that normalize each into a shared
intermediate representation (`ir.py`) and through one converter to vCon 0.4.0
core. A committed example vCon per source lives in
[`examples/sources/`](../examples/sources/) (see its `ATTRIBUTION.md`); each is
valid against **both** the JSON Schema and the CDDL grammar. Rare features were
verified present in real output: parallel tool calls (Hermes), real per-turn
timestamps + real tool errors (agent-traces), reasoning→`analysis` (SWE-rebench
`think`), reward/`resolved` outcomes (tau-bench / SWE-rebench), GUI action+
observation (Mind2Web), span-tree flattening (OpenInference). Regenerate with
`python scripts/build_source_examples.py`.

## Recommended minimal corpus (public-first)

Each row is the *owner* of at least one rare feature; together they span the space.

| # | Source | Access / License | Format | Owns (rare features) |
|---|--------|------------------|--------|----------------------|
| A | **sierra-research/tau-bench** `historical_trajectories/*.json` | Public GitHub, **MIT** | JSON | multi-turn user-simulator ↔ agent ↔ tools; OpenAI `tool_calls`+`tool` results; per-episode **`reward`**; failures (reward 0); errors as tool content |
| B | **NousResearch/hermes-function-calling-v1** | Public HF, **Apache-2.0** | parquet | **parallel tool calls** (multiple `<tool_call>` per turn); dedicated `tool` role; tool defs |
| C | **trace-commons/agent-traces** | Public HF, **CC-BY-4.0** | JSONL+parquet | **real per-event timestamps**; native captures from `claude_code`/`codex`/`cursor`/`opencode`/`pi`; full tool defs (30 sessions) |
| D | **nebius/SWE-rebench-openhands-trajectories** | Public HF, **CC-BY-4.0** | parquet (67k) | **long-horizon** code-exec trajectories; structured `tool_calls`+`tool` msgs+`tools` catalog; **`resolved`** + **`exit_status`** (incomplete/failed) |
| E | **API-Bank** (`liminghao1630/API-Bank`) | Public HF, **MIT** | JSONL | **explicit tool errors** (`exception`); multi-user-turn dialogues; auth-token dependency chains |
| F | **OpenInference / Phoenix fixtures** (`storage.googleapis.com/arize-phoenix-assets/traces/`) | Public GCS | JSONL + parquet | **nested span/subagent tree** (telemetry); `openinference.*`/`gen_ai.*` attrs; span `start_time`/`end_time` |
| G | **osunlp/Mind2Web** | Public HF, **CC-BY-4.0** | JSON | **web/GUI actions+observations** (CLICK/TYPE/SELECT + text DOM); user goal; text-first (no screenshots needed) |

### Rare-feature owners still needing heavier data or synthesis
| Feature | Best real source | Note |
|---|---|---|
| Multi-agent + **handoff/transfer** (vCon `transfer`) | `ag2ai/Agents_Failure_Attribution` ("Who&When", 127 multi-agent systems) or self-generated AutoGen GroupChat | downloadable multi-agent failure logs; true `transfer` semantics may need adapter care |
| **Multimodal/binary** (`base64url`) + **external artifact** (`url`+`content_hash`) | `osunlp/Multimodal-Mind2Web` or `OpenGVLab/GUI-Odyssey` (small slice) | heavy (GB, screenshots); take a tiny slice to exercise base64url / dereferenced content |
| Genuinely conversational 2-party web | `McGill-NLP/WebLINX` (instructor/navigator) | maps beautifully to vCon parties but **CC-BY-NC-SA** (non-commercial) |
| Explicit `incomplete` + `disposition` | approximate from D's `exit_status`/A's reward | a small **synthetic** fixture may be cleanest for the exact enum |

## Coverage matrix (corpus × feature)

Legend: ✓ = well covered · ~ = partial/embedded (needs parsing) · blank = not covered.

| Feature | A tau | B herm | C trace | D swe | E api | F oinf | G m2w | +rare |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Multi-turn | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| Long-horizon (dozens) | | | ~ | ✓ | | | ~ | |
| Multi-agent / handoff | | | | | | ~ | | ✓ (Who&When) |
| Human-in-loop / user sim | ✓ | | | | ✓ | | | |
| Structured tool calls | ✓ | ~ | ✓ | ✓ | ✓ | ✓ | ~ | |
| Tool results / observations | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| Parallel tool calls | | ✓ | | | | | | |
| Tool errors | ~ | | | ~ | ✓ | | | |
| Tool definitions | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | | |
| Explicit reasoning / CoT | | | ✓ | ✓ | | ~ | | |
| Code / JSON payloads | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | |
| Multimodal / binary | | | | | | | ~ | ✓ (MM-M2W/Odyssey) |
| Large / external artifacts | | | | ~ | | | ✓(DOM) | ✓ |
| Retries | | | ~ | ✓ | | | | |
| Incomplete / failed | ✓ | | | ✓ | ✓ | | | ✓ (Who&When) |
| Reward / success | ✓ | | | ✓ | | | | |
| Real timestamps | | | ✓ | | | ✓ | | |
| Durations | | | ~ | | | ✓ | | |
| Task spec / env metadata | ✓ | | ✓ | ✓ | | ✓ | ✓ | |
| Nested span tree | | | | | | ✓ | | |
| Flat message list | ✓ | ✓ | ✓ | ✓ | ✓ | | | |

**Every feature row is covered by at least one source.** The three that rely on
"+rare" (heavier data or synthesis): multi-agent/handoff, multimodal/binary, and
the exact `incomplete`+`disposition` enum.

## Also verified but deprioritized
- **Coding at scale (synthetic):** `nvidia/Open-SWE-Traces` (207k), `SWE-Gym/*`,
  `nebius/SWE-agent-trajectories` (ReAct free-text — needs parsing).
- **Canonical single-agent format:** SWE-agent `.traj` (MIT) — `thought`/`action`/
  `observation` steps; good CoT source; per-agent, no timestamps.
- **Tool-use, needs parsing:** ToolBench/ToolLLM (`win` label, real API obs, off-HF),
  glaive-function-calling-v2 (flat `chat` string), THUDM/AgentInstruct (ReAct).
- **Gated / non-commercial:** `Salesforce/APIGen-MT-5k` (gated, CC-BY-NC),
  `Salesforce/xlam-function-calling-60k` (single-shot, not trajectories).
- **Telemetry specs (no shipped corpus — you generate):** OpenTelemetry GenAI
  (`gen_ai.*`), LangSmith Run (`dotted_order` gives total order), OpenLLMetry,
  AutoGen `chat_history` (flat, easiest), CrewAI event stream (`parent_event_id`).
- **Environments, not JSON corpora:** WebArena/VisualWebArena/OSWorld (HTML/Playwright).

## Universal caveats
- Most ready-made files have **no per-turn timestamps** (only C and F do) — others
  synthesize monotonic order from array index.
- Many encode tool calls as **JSON-strings or XML tags** inside message text →
  each source needs its own small adapter to a common intermediate representation.
