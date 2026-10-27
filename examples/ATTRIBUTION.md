# Attribution

Every `*.vcon.json` here is a **derived work**: one real record from a public
corpus, converted by `scripts/build.py` and sliced/truncated to stay small (the
vCon's `analysis` report notes any slice). Home-directory user names and e-mail
addresses are redacted. Raw corpora are **not** vendored.

No vendor publishes an official trajectory dataset. The `anthropic/`, `openai/`
and `google/` examples are **third-party captures of each vendor's own harness**.

| Example | Harness / format | Corpus | License |
|---|---|---|---|
| `anthropic/claude-code-agent-traces` | Claude Code JSONL | [trace-commons/agent-traces](https://huggingface.co/datasets/trace-commons/agent-traces) | CC-BY-4.0 |
| `anthropic/claude-code-subagent` | Claude Code JSONL (session with a real `Task` sub-agent result → child Session) | trace-commons/agent-traces | CC-BY-4.0 |
| `anthropic/claude-code-swe-chat` | Claude Code JSONL | [SALT-NLP/SWE-chat](https://huggingface.co/datasets/SALT-NLP/SWE-chat) (via ungated mirror `cfahlgren1/SWE-chat`) | ODC-By |
| `openai/codex-cli-swe-chat` | Codex CLI rollout JSONL | SALT-NLP/SWE-chat | ODC-By |
| `google/gemini-cli-swe-chat` | Gemini CLI, SWE-chat *normalized turn rows* (no tool results) | SALT-NLP/SWE-chat | ODC-By |
| `other/terminal-bench-2-atif` | Harbor ATIF-v1.6 (`terminus-2` agent, Marin-8B model) | [AlienKevin/marin-8b-tb2-eval-traces](https://huggingface.co/datasets/AlienKevin/marin-8b-tb2-eval-traces) | Apache-2.0 |
| `other/tau-bench` | OpenAI chat-completions | [sierra-research/tau-bench](https://github.com/sierra-research/tau-bench) | MIT |
| `other/swe-rebench-openhands` | OpenHands | [nebius/SWE-rebench-openhands-trajectories](https://huggingface.co/datasets/nebius/SWE-rebench-openhands-trajectories) | CC-BY-4.0 |
| `other/hermes-function-calling` | Hermes `<tool_call>` | [NousResearch/hermes-function-calling-v1](https://huggingface.co/datasets/NousResearch/hermes-function-calling-v1) | Apache-2.0 |
| `other/mind2web` | GUI actions + DOM | [osunlp/Mind2Web](https://huggingface.co/datasets/osunlp/Mind2Web) | CC-BY-4.0 |
| `other/api-bank` | structured API calls | [API-Bank](https://github.com/AlibabaResearch/DAMO-ConvAI/tree/main/api-bank) | MIT |
| `other/openinference` | OpenTelemetry/OpenInference spans | [Arize Phoenix assets](https://github.com/Arize-ai/openinference) | Apache-2.0 |
