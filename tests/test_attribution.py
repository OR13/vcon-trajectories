"""file_attribution derivation and real-shape child sessions, on synthetic records."""
import hashlib

import pytest

from vcon_trajectories.ai_agent import utrajectory_to_vcon
from vcon_trajectories.attribution import file_attribution
from vcon_trajectories.ir import FileEdit, Hunk, MESSAGE, TOOL_CALL, Turn, UTrajectory
from vcon_trajectories.native import claude_code, codex
from vcon_trajectories.validate import CddlValidator, semantic_issues


def _ut(edits, cwd="/repo"):
    turns = [Turn(MESSAGE, "user", role="user", text="go")] + [Turn(TOOL_CALL, tool_name="Edit", call_id=f"c{i}") for i in range(len(edits))]
    return UTrajectory(source="t", id="t", turns=turns, environment={"working_dir": cwd}, file_edits=edits)


def _ranges(ut):
    fa, _ = file_attribution(ut)
    return {f["path"]: [(r["start_line"], r["end_line"]) for c in f["conversations"] for r in c["ranges"]] for f in fa["files"]}


def test_create_then_insert_shifts_later_lines():
    create = FileEdit("/repo/a.py", "create", 1, "m1", content="a\nb\nc\n")
    # insert two lines after line 1 (unified diff: old_lines=0 insertion point is the line BEFORE)
    ins = FileEdit("/repo/a.py", "update", 2, "m1",
                   hunks=[Hunk(1, 1, 1, 3, [" a", "+x", "+y"])])
    assert _ranges(_ut([create, ins])) == {"a.py": [(1, 5)]}


def test_removed_lines_lose_attribution_and_split_ranges():
    create = FileEdit("/repo/a.py", "create", 1, "m1", content="a\nb\nc\nd\n")
    rm = FileEdit("/repo/a.py", "update", 2, "m1", hunks=[Hunk(2, 2, 1, 0, ["-b", "-c"])])  # unified diff: "+1,0" means "after line 1"
    assert _ranges(_ut([create, rm])) == {"a.py": [(1, 2)]}  # a, d(now line 2) are contiguous


def test_human_lines_between_ai_edits_stay_unattributed():
    # no create: the file pre-exists with human lines; agent only adds line 2
    ed = FileEdit("/repo/a.py", "update", 1, "m1", hunks=[Hunk(1, 2, 1, 3, [" h1", "+ai", " h2"])])
    assert _ranges(_ut([ed])) == {"a.py": [(2, 2)]}


def test_two_models_get_per_range_contributors_and_hash_is_sha256_of_lines():
    e1 = FileEdit("/repo/a.py", "create", 1, "m1", content="a\nb\n")
    e2 = FileEdit("/repo/a.py", "update", 2, "m2", hunks=[Hunk(2, 1, 2, 2, [" b", "+z"])])
    fa, stats = file_attribution(_ut([e1, e2]))
    conv = fa["files"][0]["conversations"][0]
    assert "contributor" not in conv and [r["contributor"]["model_id"] for r in conv["ranges"]] == ["m1", "m2"]
    assert conv["ranges"][1]["content_hash"] == hashlib.sha256(b"z").hexdigest()


def test_outside_working_dir_and_delete_are_excluded():
    edits = [FileEdit("/elsewhere/x.py", "create", 1, "m", content="x\n"),
             FileEdit("/repo/gone.py", "create", 1, "m", content="x\n"),
             FileEdit("/repo/gone.py", "delete", 2, "m")]
    fa, stats = file_attribution(_ut(edits))
    assert fa is None and stats["files_outside_working_dir"] == 1


def test_windows_paths_relativize_case_insensitively():
    e = FileEdit("D:\\Proj\\src\\a.py", "create", 1, "m", content="x\n")
    assert _ranges(_ut([e], cwd="d:\\proj")) == {"src/a.py": [(1, 1)]}


def _valid(v):
    try:
        c = CddlValidator()
    except Exception:
        pytest.skip("ruby cddl gem not available")
    ok, msg = c.validate(v)
    assert ok, msg
    assert semantic_issues(v) == []


def test_claude_write_edit_and_task_result_end_to_end():
    T = "2026-06-12T00:00:%02d.000Z"
    recs = [
        {"type": "user", "uuid": "u1", "parentUuid": None, "sessionId": "s", "cwd": "/repo", "timestamp": T % 0,
         "message": {"role": "user", "content": "do it"}},
        {"type": "assistant", "uuid": "a1", "parentUuid": "u1", "timestamp": T % 1,
         "message": {"id": "m1", "model": "claude-opus-4-5", "content": [
             {"type": "tool_use", "id": "w1", "name": "Write", "input": {}},
             {"type": "tool_use", "id": "t1", "name": "Task", "input": {"prompt": "look"}}]}},
        {"type": "user", "uuid": "u2", "parentUuid": "a1", "timestamp": T % 5,
         "toolUseResult": {"type": "create", "filePath": "/repo/a.py", "content": "a\nb\n", "structuredPatch": []},
         "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "w1", "content": "ok"}]}},
        {"type": "user", "uuid": "u3", "parentUuid": "u2", "timestamp": T % 20,
         "toolUseResult": {"status": "completed", "prompt": "look", "agentId": "abc", "agentType": "Explore",
                           "content": [{"type": "text", "text": "done"}], "totalDurationMs": 10000,
                           "totalTokens": 99, "totalToolUseCount": 3, "usage": {"input_tokens": 1}},
         "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "done"}]}},
    ]
    v = utrajectory_to_vcon(claude_code.parse(recs))
    assert v["file_attribution"]["files"][0]["path"] == "a.py"
    assert v["file_attribution"]["files"][0]["conversations"][0]["contributor"]["model_id"] == "claude-opus-4-5"
    assert len(v["sessions"]) == 2
    child = v["sessions"][1]
    assert child["agent_session_id"] == "abc" and child["duration"] == 10.0
    assert "call t1" in v["sessions"][0]["sessions"][0]["description"]
    assert [e["event_type"] for e in v["events"] if e["session"] == 1] == ["subagent-start", "subagent-end"]
    _valid(v)


def test_codex_patch_apply_end_becomes_replayed_edit():
    recs = [
        {"type": "session_meta", "payload": {"id": "c", "cwd": "/repo", "model_provider": "openai"}},
        {"type": "turn_context", "payload": {"model": "gpt-5-codex"}},
        {"type": "response_item", "timestamp": "2026-03-01T00:00:00.000Z",
         "payload": {"type": "custom_tool_call", "name": "apply_patch", "call_id": "p1", "input": "*** Begin Patch"}},
        {"type": "event_msg", "timestamp": "2026-03-01T00:00:01.000Z",
         "payload": {"type": "patch_apply_end", "call_id": "p1", "success": True,
                     "changes": {"/repo/n.txt": {"type": "add", "content": "one\ntwo\n"},
                                 "/repo/m.txt": {"type": "update", "unified_diff": "@@ -1,2 +1,3 @@\n a\n+b\r\n c\n"}}}},
    ]
    v = utrajectory_to_vcon(codex.parse(recs))
    got = {f["path"]: f["conversations"][0]["ranges"][0] for f in v["file_attribution"]["files"]}
    assert (got["n.txt"]["start_line"], got["n.txt"]["end_line"]) == (1, 2)
    assert (got["m.txt"]["start_line"], got["m.txt"]["end_line"]) == (2, 2)
    assert got["m.txt"]["content_hash"] == hashlib.sha256(b"b").hexdigest()  # CRLF normalized
