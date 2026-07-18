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

## A separate, structured dataset: `VINAY-UMRETHE/Mythos-Agent`

> **This is a different, unrelated artifact.** It is *not* the training data of
> the Qwythos model above (those traces are proprietary). It is an independent
> Hugging Face **dataset** that happens to share the "mythos" name. Do not
> conflate the two.

- **Dataset:** [`VINAY-UMRETHE/Mythos-Agent`](https://huggingface.co/datasets/VINAY-UMRETHE/Mythos-Agent)
- **License:** CC-BY-4.0 · **Size:** 65 rows, one `train` split, single Parquet
  file (`data/train-00000-of-00001.parquet`)
- **Shape:** structured agent trajectories — top-level `id`, `schema_version`,
  `model_target`, `created_at`, `metadata`, `system`, `tools[]`, and
  `messages[]` (`role` + `content`), following the Anthropic Messages
  convention (`content` blocks of `text` / `tool_use` / `tool_result`).
- **Access:** the repo is **gated** (approval required). A valid `HF_TOKEN`
  authenticates you, but you must *also* be on the authorized list, or downloads
  fail with `GatedRepoError` (403 "not in the authorized list"). Request access
  on the dataset page while logged in, wait for approval, then:

```bash
export HF_TOKEN=hf_...   # a token for an account that has been granted access
python - <<'PY'
from huggingface_hub import hf_hub_download
import pyarrow.parquet as pq
p = hf_hub_download("VINAY-UMRETHE/Mythos-Agent",
                    "data/train-00000-of-00001.parquet",
                    repo_type="dataset", token=True)
print(pq.read_table(p).num_rows, "rows")
PY
```

**Status in this repo:** not yet consumed — access to the gate was still pending
at last check. A structured parser for this shape can be added under
`src/vcon_trajectories/` once access is granted; the existing `convert.py`
(Trajectory → vCon) is source-agnostic and can be reused directly.

The primary, reproducible demo uses the **public** Qwythos eval logs above so it
runs with no auth.
