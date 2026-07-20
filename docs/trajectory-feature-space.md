# Agent trajectory feature space → vCon coverage

The goal of the evaluation corpus is not "one big dataset" but a **minimal set of
real, public JSON trajectories whose union exercises every feature below**, so the
trajectory→vCon mapping is stress-tested on every shape it will encounter.

Each feature lists the vCon construct it stresses. Candidate sources scored
against these dimensions live in the coverage matrix
([`docs/trajectory-sources.md`](trajectory-sources.md)).

## Coverage dimensions

### 1. Conversation structure
| Feature | vCon stressor |
|---|---|
| Single-turn | trivial `dialog[]` |
| Multi-turn | ordered `dialog[]` |
| Long-horizon (dozens of steps) | large `dialog[]`, index cross-refs |
| Multi-agent / sub-agents | multiple `bot` parties |
| Agent handoff / delegation | `dialog.type:"transfer"` (transferor/transferee/transfer_target) |
| Human-in-the-loop mid-run | mixed person/bot `originator` |

### 2. Roles & parties
| Feature | vCon stressor |
|---|---|
| system / user / assistant | party `type` person/bot |
| distinct tools / environment | party `type` bot/organization; tool-as-party |
| organizations / services | party `type:"organization"` |

### 3. Tool interaction
| Feature | vCon stressor |
|---|---|
| Structured tool call + arguments | `dialog` body `encoding:"json"`, `application` |
| Tool result / observation | tool-originated `dialog` |
| Tool errors | error payload in body |
| Parallel tool calls (fan-out in one turn) | multiple `dialog` from one turn |
| Tool / function definitions | `attachments` (purpose `tool-definitions`) |

### 4. Reasoning
| Feature | vCon stressor |
|---|---|
| Explicit thinking / CoT separate from output | `analysis` (schema `chain-of-thought`) |

### 5. Content & modality
| Feature | vCon stressor |
|---|---|
| Plain text | `encoding:"none"` |
| Code / JSON payloads | `encoding:"json"` |
| Binary / multimodal (screenshots, audio) | `encoding:"base64url"` |
| Large artifacts | external `url` + `content_hash` (dereferenced content) |

### 6. Control flow & outcome
| Feature | vCon stressor |
|---|---|
| Retries | repeated tool `dialog` entries |
| Failure / aborted / incomplete run | `dialog.type:"incomplete"` + `disposition` |
| Reward / success / score / rubric | `analysis` (type `report`) |

### 7. Timing & provenance
| Feature | vCon stressor |
|---|---|
| Real per-step timestamps | `dialog.start` from source (not synthesized) |
| Durations | `dialog.duration` |
| Task spec / environment metadata | `attachments` / `analysis` |

### 8. Structure shape
| Feature | vCon stressor |
|---|---|
| Flat message list | direct `dialog[]` |
| Nested span / subagent trees (telemetry) | flatten to flat `dialog[]` + cross-refs |

## Status of coverage today

From the sources already wired up:
- **Qwythos eval logs** (public): multi-turn, tool call+result, tool errors,
  chain-of-thought, text/json content, tool-definitions, single-turn samples.
- **VINAY-UMRETHE/Mythos-Agent** (gated): structured multi-turn, tool_use/
  tool_result, system prompt, real timestamps, tool schemas.

**Known gaps** to fill with new sources (the rare, high-value shapes):
- Agent **handoff / transfer** (`transfer` dialog type)
- **Incomplete / failed** runs (`incomplete` + `disposition`)
- **Parallel** tool calls
- **Multimodal** content (base64url) and **external artifact** references (url + content_hash)
- **Nested span/subagent trees** (telemetry flattening)
- **Long-horizon** (dozens of steps) trajectories with real timestamps
