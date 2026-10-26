# Vendor-native trajectories → `ai_agent` vCon

How each native format is parsed (`src/vcon_trajectories/native/`) and mapped
(`src/vcon_trajectories/ai_agent.py`). Everything below was checked against the real
corpora in [`corpus-report.md`](corpus-report.md); where the mapping is a judgment call it says so.

## Anthropic — Claude Code session JSONL

Source: `native/claude_code.py`. One JSON object per line; `user` / `assistant` / `system`
records are mapped, the rest are counted as unmapped.

| Native | vCon | Note |
|---|---|---|
| `user` with string / `text` block | `dialog` text, party `user` | |
| `assistant` `text` block | `dialog` text + `model_id`, `token_usage`, `entry_id`, `parent_id` | |
| `thinking` block | `reasoning` event, `content` | |
| `redacted_thinking.data` | `reasoning.encrypted` (`content` = "") | |
| `thinking.signature` | **not mapped** | an integrity token for replay, not ciphertext; counted as unmapped |
| `tool_use` | `tool-call` (`call_id` = block `id`) | |
| `tool_result` | `tool-result` (`call_id`, `is_error`, `status`) | |
| `system` record | `system-event`, `event_type` = `subtype` | |
| `message.usage` on a turn with **no** `text` block | `system-event` `token-count` | `Dialog.token_usage` has nowhere to live — see feedback |
| `uuid` / `parentUuid` | `entry_id` / `parent_id` | parents that point at skipped records are **re-linked** to the nearest mapped ancestor |
| `isSidechain` | child `Session` + Session_Reference `child` | **synthetic test only**: real corpora have no inline sidechains |
| `cwd`, `gitBranch`, `version`, `message.model` | `environment`, `vcs`, `agent_meta` | provider fixed to `anthropic` |

One streamed assistant message is split over several records repeating `message.id`
and `usage`; usage is taken once per `message.id`.

## OpenAI — Codex CLI rollout JSONL

Source: `native/codex.py`.

| Native | vCon | Note |
|---|---|---|
| `response_item` `message` (user) | `dialog` text | injected context (`<environment_context>`, `# AGENTS.md`) → `system-event` `context-injection` |
| `response_item` `message` (developer) | `system-event` `developer-instructions` | |
| `response_item` `message` (assistant) | `dialog` text + `model_id` | |
| `reasoning` | `reasoning` event: `content` = summary, `encrypted` = `encrypted_content` | most real sessions carry encrypted reasoning |
| `function_call` / `function_call_output` | `tool-call` / `tool-result` (`call_id`) | |
| `event_msg.exec_command_end` | sets `is_error` / `status` on the matching result | exit code ≠ 0 → error |
| `event_msg.token_count` | `system-event` `token-count` | |
| `task_started` / `task_complete` / `turn_aborted` | `system-event` | |
| `user_message`, `agent_message` | skipped (duplicate of `response_item`) | counted |
| `patch_apply_end`, `mcp_tool_call_end`, `web_search_*`, `compacted`, review-mode events | **not mapped** | counted; candidates for `file_attribution` / new event types |

No entry ids exist natively, so no `entry_id` / `parent_id`.

## Google — Gemini CLI (normalized rows only)

Source: `native/gemini_cli.py`. **SWE-chat's table, not raw logs**: user prompts,
assistant responses (with tokens), and `tool_use` rows with Gemini-native tool names
(`run_shell_command`, `write_file`, `replace`). **No tool results, no reasoning.** Raw
Gemini CLI session logs and ADK `Event` streams are not covered.

## Non-vendor corpora

`sources/adapters.py` maps tau-bench and SWE-rebench (OpenAI-style chat + tools), Hermes,
Mind2Web (GUI `ACTION`/`OBSERVATION` → `tool-call`/`tool-result`), API-Bank and
OpenInference spans onto the same IR. They exercise shapes vendors' CLIs don't produce
(GUI actions, telemetry trees, tool definitions as `attachments`).
