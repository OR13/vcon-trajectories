"""Offline tests on tiny SYNTHETIC records shaped like the native formats.
(Real-data validation is `scripts/build.py --report`.)"""
import pytest

from vcon_trajectories.ai_agent import utrajectory_to_vcon
from vcon_trajectories.native import claude_code, codex, gemini_cli
from vcon_trajectories.validate import CddlValidator, semantic_issues


def _valid(vcon):
    try:
        v = CddlValidator()
    except Exception:
        pytest.skip("ruby cddl gem not available")
    ok, msg = v.validate(vcon)
    assert ok, msg
    assert semantic_issues(vcon) == []


def _cc():
    T = "2026-06-12T00:00:0%d.000Z"
    return [
        {"type": "user", "uuid": "u1", "parentUuid": None, "sessionId": "s1", "cwd": "/Users/x/p", "gitBranch": "main",
         "version": "2.1.0", "timestamp": T % 0, "message": {"role": "user", "content": "hi"}},
        {"type": "attachment", "uuid": "att", "parentUuid": "u1", "timestamp": T % 1},
        {"type": "assistant", "uuid": "a1", "parentUuid": "att", "timestamp": T % 2,
         "message": {"id": "m1", "model": "claude-opus-4-5", "usage": {"input_tokens": 5, "output_tokens": 7, "cache_read_input_tokens": 3},
                     "content": [{"type": "thinking", "thinking": "hmm"}]}},
        {"type": "assistant", "uuid": "a2", "parentUuid": "a1", "timestamp": T % 3,
         "message": {"id": "m1", "model": "claude-opus-4-5", "usage": {"input_tokens": 5, "output_tokens": 7},
                     "content": [{"type": "tool_use", "id": "t1", "name": "Task", "input": {"prompt": "x"}},
                                 {"type": "tool_use", "id": "t2", "name": "Read", "input": {"p": 1}}]}},
        {"type": "user", "uuid": "u2", "parentUuid": "a2", "timestamp": T % 4,
         "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t2", "content": "boom", "is_error": True}]}},
        {"type": "assistant", "uuid": "s1a", "parentUuid": "a2", "isSidechain": True, "agentId": "ag1", "timestamp": T % 5,
         "message": {"id": "m2", "model": "claude-opus-4-5", "content": [{"type": "text", "text": "sub-agent says hi"}]}},
    ]


def test_claude_code_mapping():
    ut = claude_code.parse(_cc())
    v = utrajectory_to_vcon(ut)
    types = [e["type"] for e in v["events"]]
    assert types.count("tool-call") == 2 and "reasoning" in types
    # usage counted once, on a token-count event (no text message in that turn)
    tc = [e for e in v["events"] if e.get("event_type") == "token-count"]
    assert len(tc) == 1 and tc[0]["data"]["input"] == 8  # 5 + 3 cache reads: input is normalized to include cached
    # skipped attachment record is bridged: a1's parent is u1, not the attachment
    a1 = next(e for e in v["events"] if e.get("entry_id") == "a1")
    assert a1["parent_id"] == "u1"
    err = next(e for e in v["events"] if e["type"] == "tool-result")
    assert err["is_error"] is True and err["call_id"] == "t2"
    # sidechain -> child session referenced from the main session
    assert len(v["sessions"]) == 2
    assert v["sessions"][0]["sessions"] == [{"session": 1, "type": "child"}]
    assert v["parties"][1]["agent_meta"]["model_provider"] == "anthropic"
    assert v["sessions"][0]["environment"]["working_dir"] == "/Users/x/p"
    _valid(v)


def test_codex_mapping():
    recs = [
        {"timestamp": "2026-04-02T05:33:38.732Z", "type": "session_meta",
         "payload": {"id": "c1", "cwd": "/w", "cli_version": "0.118.0", "model_provider": "openai",
                     "git": {"commit_hash": "abc", "branch": "main"}}},
        {"timestamp": "2026-04-02T05:33:38.733Z", "type": "turn_context", "payload": {"model": "gpt-5-codex"}},
        {"timestamp": "2026-04-02T05:33:39.000Z", "type": "response_item",
         "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "list"}]}},
        {"timestamp": "2026-04-02T05:33:40.000Z", "type": "response_item",
         "payload": {"type": "reasoning", "summary": [], "content": None, "encrypted_content": "gAAAA"}},
        {"timestamp": "2026-04-02T05:33:41.000Z", "type": "response_item",
         "payload": {"type": "function_call", "name": "exec_command", "arguments": "{\"cmd\":\"false\"}", "call_id": "k1"}},
        {"timestamp": "2026-04-02T05:33:42.000Z", "type": "response_item",
         "payload": {"type": "function_call_output", "call_id": "k1", "output": "exit 1"}},
        {"timestamp": "2026-04-02T05:33:42.100Z", "type": "event_msg",
         "payload": {"type": "exec_command_end", "call_id": "k1", "exit_code": 1}},
    ]
    v = utrajectory_to_vcon(codex.parse(recs))
    r = next(e for e in v["events"] if e["type"] == "reasoning")
    assert r["content"] == "" and r["encrypted"] == "gAAAA"
    res = next(e for e in v["events"] if e["type"] == "tool-result")
    assert res["is_error"] is True and res["status"] == "error"
    call = next(e for e in v["events"] if e["type"] == "tool-call")
    assert call["input"] == {"cmd": "false"}
    assert v["vcs"]["revision"] == "abc" and v["parties"][1]["agent_meta"]["model_id"] == "gpt-5-codex"
    _valid(v)


def test_gemini_rows():
    rows = [
        {"session_id": "g1", "turn_number": "0", "turn_type": "user_prompt", "content": "make a dir", "timestamp": "2026-03-18 21:56:57.632000+00:00"},
        {"session_id": "g1", "turn_number": "1", "turn_type": "tool_use", "tool_name": "run_shell_command",
         "tool_call_id": "run-1", "tool_input_json": "{\"command\": \"mkdir x\"}", "timestamp": "2026-03-18 21:57:19.433000+00:00"},
        {"session_id": "g1", "turn_number": "2", "turn_type": "assistant_response", "content": "done", "model": "gemini-2.5-pro",
         "input_tokens": "10", "output_tokens": "2", "timestamp": "2026-03-18 21:57:48.805000+00:00"},
    ]
    v = utrajectory_to_vcon(gemini_cli.parse(rows))
    assert v["events"][0]["tool_name"] == "run_shell_command"
    assert v["dialog"][1]["token_usage"] == {"input": 10, "output": 2}
    _valid(v)


def test_untimestamped_turns_are_flagged():
    from vcon_trajectories.ir import MESSAGE, TOOL_CALL, Turn, UTrajectory
    v = utrajectory_to_vcon(UTrajectory(source="t", id="1", turns=[
        Turn(MESSAGE, "user", role="user", text="a"), Turn(TOOL_CALL, tool_name="x", tool_input={})]))
    assert v["analysis"][0]["body"]["timestamps_synthesized"] == 2
    _valid(v)
