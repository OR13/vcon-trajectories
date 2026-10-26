"""Fetch real public trajectory corpora (cached under .cache/corpora, git-ignored).

Vendor-native session logs (the point of this repo):
  anthropic  trace-commons/agent-traces   sessions/claude_code/*.jsonl   CC-BY-4.0
  anthropic  SALT-NLP/SWE-chat (mirror cfahlgren1/SWE-chat) Claude Code    ODC-By
  openai     SWE-chat Codex CLI rollouts                                   ODC-By
  google     SWE-chat Gemini CLI turn rows (normalized, no tool results)   ODC-By
No vendor publishes an official trajectory dataset; these are third-party captures
of the vendors' own harnesses.
"""
import json
import os
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(HERE, ".cache", "corpora")
HF = "https://huggingface.co"
UA = {"User-Agent": "vcon-trajectories/0.2"}


def get(url: str, retries: int = 3) -> bytes:
    key = os.path.join(CACHE, urllib.parse.quote(url, safe=""))[:240]
    if os.path.exists(key):
        return open(key, "rb").read()
    err = None
    for i in range(retries):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read()
            os.makedirs(CACHE, exist_ok=True)
            open(key, "wb").write(data)
            return data
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"GET {url}: {err}")


def jsonl(b: bytes):
    return [json.loads(l) for l in b.decode("utf-8", "replace").splitlines() if l.strip()]


# --- Anthropic: trace-commons/agent-traces --------------------------------------
def agent_traces_claude(n: int):
    tree = json.loads(get(f"{HF}/api/datasets/trace-commons/agent-traces/tree/main/sessions/claude_code"))
    files = sorted(t["path"] for t in tree if t["path"].endswith(".jsonl") and "comparia" not in t["path"])
    for p in files[:n]:
        yield os.path.basename(p)[:-6], jsonl(get(f"{HF}/datasets/trace-commons/agent-traces/resolve/main/{p}"))


# --- SWE-chat mirror ---------------------------------------------------------------
def _swechat_sessions():
    import pyarrow.parquet as pq
    path = os.path.join(CACHE, "swechat_sessions.parquet")
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        open(path, "wb").write(get(f"{HF}/datasets/cfahlgren1/SWE-chat/resolve/main/sessions.parquet"))
    return pq.read_table(path, columns=["session_id", "agent", "turn_count", "tool_call_count"]).to_pylist()


def swechat_native(agent: str, n: int, max_turns: int = 40, min_turns: int = 2):
    rows = [r for r in _swechat_sessions() if r["agent"] == agent and r["turn_count"]
            and min_turns <= r["turn_count"] <= max_turns]
    rows.sort(key=lambda r: (-(r["tool_call_count"] or 0) if agent != "Codex" else -r["turn_count"], r["session_id"]))
    got = 0
    for r in rows:
        if got >= n:
            break
        try:
            recs = jsonl(get(f"{HF}/datasets/cfahlgren1/SWE-chat/resolve/main/traces/{r['session_id']}.jsonl"))
        except RuntimeError:
            continue  # mirror only carries some transcripts
        got += 1
        yield r["session_id"], recs


def _gemini_rows():
    """All Gemini CLI turn rows. The datasets-server filter API is unreliable, so scan
    conversations.parquet (1.3 GB, downloaded once into .cache) and keep a small extract."""
    extract = os.path.join(CACHE, "swechat_gemini_rows.json")
    if os.path.exists(extract):
        return json.load(open(extract))
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    big = os.path.join(CACHE, "swechat_conversations.parquet")
    if not os.path.exists(big):
        os.makedirs(CACHE, exist_ok=True)
        req = urllib.request.Request(f"{HF}/datasets/cfahlgren1/SWE-chat/resolve/main/conversations.parquet", headers=UA)
        with urllib.request.urlopen(req, timeout=600) as r, open(big, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
    pf = pq.ParquetFile(big)
    rows = []
    for g in range(pf.num_row_groups):
        t = pf.read_row_group(g)
        rows += t.filter(pc.equal(t["agent"], pa.scalar("Gemini CLI"))).to_pylist()
    json.dump(rows, open(extract, "w"), default=str)
    return rows


def swechat_gemini(n: int):
    """Gemini CLI sessions only exist as normalized turn rows (conversations table)."""
    by = {}
    for r in _gemini_rows():
        by.setdefault(r["session_id"], []).append(r)
    ids = sorted(i for i, rs in by.items() if any(x["turn_type"] == "tool_use" for x in rs) and len(rs) <= 60)
    for i in ids[:n]:
        yield i, by[i]
