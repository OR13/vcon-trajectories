"""Derive the draft's `file_attribution` from the file edits an agent harness recorded.

Input: `UTrajectory.file_edits` (Claude Code Edit/Write results with `structuredPatch`, Codex
`patch_apply_end` unified diffs). Each edit is replayed in order against a per-file map
`line number -> (text, model)` of the lines THIS session authored, so line numbers stay correct as
later edits shift earlier ones. Unchanged context lines keep their provenance, removed lines drop it,
added lines are attributed to the model that issued the edit.

What this can and cannot say:
- Only lines the agent wrote are attributed (`contributor.type = "ai"`). Lines a human edited outside
  the session, or that were never touched, are absent, so the ranges are a lower bound on AI authorship
  of the file, not a partition of it.
- Line numbers are those after the LAST recorded edit, not necessarily the committed file.
- `content_hash` is SHA-256 over the range's lines joined with "\\n" (CRLF normalized, no trailing
  newline). The draft does not define the canonicalization; this is this repo's choice.
- Paths are made relative to the session's working directory; edits outside it are skipped and counted.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Tuple

from .ir import FileEdit, UTrajectory

Line = Tuple[str, Optional[str]]  # (text, model)


def _apply_hunks(state: Dict[int, Line], edit: FileEdit) -> Dict[int, Line]:
    out: Dict[int, Line] = {}
    old_keys = sorted(state)
    i = 0
    cursor, delta = 1, 0

    def carry_until(limit: Optional[int]) -> None:
        nonlocal i
        while i < len(old_keys) and (limit is None or old_keys[i] < limit):
            ln = old_keys[i]
            if ln >= cursor:
                out[ln + delta] = state[ln]
            i += 1

    for h in edit.hunks:
        first_old = h.old_start if h.old_lines > 0 else h.old_start + 1
        carry_until(first_old)
        o = first_old
        n = h.new_start if h.new_lines > 0 else h.new_start + 1
        for line in h.lines:
            mark, text = line[:1], line[1:].rstrip("\r")
            if mark == " ":
                if o in state:
                    out[n] = state[o]
                o += 1
                n += 1
            elif mark == "-":
                o += 1
            elif mark == "+":
                out[n] = (text, edit.model)
                n += 1
        # skip old keys consumed by the hunk, then continue from after it
        while i < len(old_keys) and old_keys[i] < o:
            i += 1
        cursor, delta = o, n - o
    carry_until(None)
    return out


def _relative(path: str, cwd: Optional[str]) -> Optional[str]:
    p = path.replace("\\", "/")
    if cwd:
        c = cwd.replace("\\", "/").rstrip("/")
        if p.lower().startswith(c.lower() + "/"):
            return p[len(c) + 1:]
    if p.startswith("/") or (len(p) > 1 and p[1] == ":"):
        return None  # absolute path outside the working directory
    return p


def _runs(state: Dict[int, Line]) -> List[Tuple[int, int, Optional[str], List[str]]]:
    runs: List[Tuple[int, int, Optional[str], List[str]]] = []
    for ln in sorted(state):
        text, model = state[ln]
        if runs and runs[-1][1] == ln - 1 and runs[-1][2] == model:
            s, _, m, t = runs[-1]
            runs[-1] = (s, ln, m, t + [text])
        else:
            runs.append((ln, ln, model, [text]))
    return runs


def file_attribution(ut: UTrajectory) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """Return (`file_attribution` object or None, stats for the analysis report)."""
    cwd = (ut.environment or {}).get("working_dir")
    files: Dict[str, Dict[int, Line]] = {}
    outside = set()
    for e in ut.file_edits:
        if e.turn_index >= len(ut.turns):
            continue
        rel = _relative(e.path, cwd)
        if rel is None:
            outside.add(e.path)
            continue
        if e.kind == "delete":
            files.pop(rel, None)
        elif e.kind == "create":
            text = (e.content or "").replace("\r\n", "\n")
            lines = text.split("\n")
            if lines and lines[-1] == "":
                lines.pop()
            files[rel] = {i + 1: (t, e.model) for i, t in enumerate(lines)}
        else:
            files[rel] = _apply_hunks(files.get(rel, {}), e)

    out_files = []
    for rel in sorted(files):
        runs = _runs(files[rel])
        if not runs:
            continue
        models = {m for _, _, m, _ in runs}
        single = len(models) == 1
        ranges = []
        for s, e_, m, texts in runs:
            r: Dict[str, Any] = {"start_line": s, "end_line": e_,
                                 "content_hash": hashlib.sha256("\n".join(texts).encode("utf-8")).hexdigest(),
                                 "content_hash_alg": "sha-256"}
            if not single:
                r["contributor"] = _contributor(m)
            ranges.append(r)
        conv: Dict[str, Any] = {"ranges": ranges}
        if single:
            conv["contributor"] = _contributor(next(iter(models)))
        out_files.append({"path": rel, "conversations": [conv]})
    stats = {"file_edits_replayed": len(ut.file_edits), "files_outside_working_dir": len(outside) or None,
             "attributed_files": len(out_files),
             "attributed_lines": sum(r["end_line"] - r["start_line"] + 1 for f in out_files
                                     for r in f["conversations"][0]["ranges"])}
    return ({"files": out_files} if out_files else None), stats


def _contributor(model: Optional[str]) -> Dict[str, Any]:
    return {"type": "ai", **({"model_id": model} if model else {})}
