# Attribution for source-example vCons

Each `*.vcon.json` in this directory is a **derived work**: a single real record
from a public dataset, converted to an IETF vCon (v0.4.0) by
`scripts/build_source_examples.py` via the adapters in
`src/vcon_trajectories/sources/`. Records are sliced to keep examples small
(`analysis` metadata notes any truncation). Raw datasets are **not** vendored.

| Example file | Source dataset | License | URL |
|---|---|---|---|
| `tau-bench.vcon.json` | sierra-research/tau-bench (`historical_trajectories`) | MIT | https://github.com/sierra-research/tau-bench |
| `swe-rebench.vcon.json` | nebius/SWE-rebench-openhands-trajectories | CC-BY-4.0 | https://huggingface.co/datasets/nebius/SWE-rebench-openhands-trajectories |
| `agent-traces.vcon.json` | trace-commons/agent-traces | CC-BY-4.0 | https://huggingface.co/datasets/trace-commons/agent-traces |
| `hermes-function-calling.vcon.json` | NousResearch/hermes-function-calling-v1 | Apache-2.0 | https://huggingface.co/datasets/NousResearch/hermes-function-calling-v1 |
| `mind2web.vcon.json` | osunlp/Mind2Web | CC-BY-4.0 | https://huggingface.co/datasets/osunlp/Mind2Web |
| `api-bank.vcon.json` | liminghao1630/API-Bank (Alibaba DAMO-ConvAI) | MIT | https://github.com/AlibabaResearch/DAMO-ConvAI/tree/main/api-bank |
| `openinference.vcon.json` | Arize Phoenix example traces (`arize-phoenix-assets`) | Apache-2.0 (OpenInference) | https://github.com/Arize-ai/openinference |

All licenses above permit redistribution of derivatives with attribution. The
vCon `analysis` entry of type `report` / schema `trajectory-metadata` in each
file also records the originating `source` and record `id`.

To regenerate: `python scripts/build_source_examples.py` (fetches the records
again from the public routes above; no authentication required).
