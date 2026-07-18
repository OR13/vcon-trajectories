# Getting the Mythos trajectory data

## TL;DR

The repo `empero-ai/Qwythos-9B-Claude-Mythos-5-1M` is a **model**, not a dataset.
Its actual training traces ("Claude Mythos and Claude Fable traces … generated
in-house by `rethink`") are **proprietary and not published** — there is no
`datasets:` link and no downloadable trajectory dataset in it.

What *is* public and downloadable are the model's **evaluation logs**, which are
real multi-turn / tool-use trajectories produced by the Mythos model. Those are
what this project converts to vCons:

```
evals/sample_generations.md   # 25 single-turn generations (reasoning + answer)
evals/tool_test_outputs.md    # 7 agentic tool-use trajectories (thinking→tool→result→answer)
evals/retest_outputs.md
```

## How to download (no token needed — public model repo)

```bash
pip install huggingface_hub
python - <<'PY'
from huggingface_hub import hf_hub_download
import shutil, os
repo = "empero-ai/Qwythos-9B-Claude-Mythos-5-1M"
for f in ["evals/sample_generations.md", "evals/tool_test_outputs.md", "evals/retest_outputs.md"]:
    p = hf_hub_download(repo_id=repo, filename=f, repo_type="model")
    os.makedirs("data/qwythos_evals", exist_ok=True)
    shutil.copy(p, os.path.join("data/qwythos_evals", os.path.basename(f)))
PY
```

Equivalent CLI: `hf download empero-ai/Qwythos-9B-Claude-Mythos-5-1M evals/tool_test_outputs.md --repo-type model --local-dir data/`

The weights (`model.safetensors`, ~9B params) are large; you do **not** need them —
only the `evals/*.md` files.

## About the other "mythos" dataset

`VINAY-UMRETHE/Mythos-Agent` is a genuine HF *dataset* of agent trajectories
(65 rows, parquet, Anthropic messages/tool-call shape), but it is **gated**
(HTTP 401 without an accepted access request + `HF_TOKEN`). If you want to use it
instead, accept the gate on huggingface.co, `export HF_TOKEN=...`, and it can be
loaded with `datasets.load_dataset("VINAY-UMRETHE/Mythos-Agent")`. This project
uses the public Qwythos eval logs so the demo is fully reproducible with no auth.
