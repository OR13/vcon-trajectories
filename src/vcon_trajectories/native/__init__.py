"""Parsers for vendor-native agent session logs -> `UTrajectory`.

- `claude_code`: Anthropic Claude Code session JSONL (also the Agent SDK message shape)
- `codex`:       OpenAI Codex CLI rollout JSONL (Responses-API items + event_msg)
- `gemini_cli`:  Google Gemini CLI sessions as normalized by SWE-chat (turn rows)
"""
