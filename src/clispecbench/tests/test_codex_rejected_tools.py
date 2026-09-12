import copy
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from clispecbench.agents.codex_rejected_tools import supplement
from clispecbench.agents.codex_tool_evidence import scan


def pair(
    source: str = 'const r = await tools.exec_command({cmd:"rm -f /tmp/test"}); text(r.output);',
) -> dict[str, Any]:
    request = {"type": "custom_tool_call", "name": "exec", "call_id": "c", "input": source}
    output = {
        "type": "custom_tool_call_output",
        "call_id": "c",
        "output": [
            {"type": "input_text", "text": "Script failed\nWall time 0.0 seconds\nOutput:\n"},
            {
                "type": "input_text",
                "text": (
                    "Script error:\nexec_command failed: CreateProcess "
                    '{ message: "Rejected(cleanup)" }'
                ),
            },
        ],
    }
    return {
        "call_id": "c",
        "requests": [{"path": "session", "line": 1, "payload": request}],
        "rejection_output": {"path": "session", "line": 2, "payload": output},
    }


class CountingTests(unittest.TestCase):
    def audit(
        self,
        rejections: list[dict[str, Any]] | None = None,
        canonical: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (),
    ) -> dict[str, Any]:
        return {
            "rejections": [pair()] if rejections is None else rejections,
            "canonical_items": list(canonical),
            "session_files": 1,
            "canonical_events_present": True,
        }

    def test_one_explicit_runtime_rejection_adds_one(self) -> None:
        r = supplement(self.audit(), 12)
        self.assertTrue(r["available"])
        self.assertEqual(r["corrected_tool_calls"], 13)

    def test_text_await_shape_is_supported(self) -> None:
        a = self.audit(
            [
                pair(
                    'text(await tools.exec_command({cmd:"rm -f /tmp/test",'
                    "max_output_tokens:3000}));"
                )
            ]
        )
        self.assertEqual(supplement(a, 12)["corrected_tool_calls"], 13)

    def test_byte_identical_duplicates_do_not_double_count(self) -> None:
        p = pair()
        duplicate = copy.deepcopy(p)
        duplicate["requests"][0]["path"] = "copied-session"
        duplicate["rejection_output"]["path"] = "copied-session"
        a = self.audit([p, duplicate])
        self.assertEqual(supplement(a, 12)["corrected_tool_calls"], 13)

    def test_unpaired_conflicting_output_or_multiple_attempts_are_unavailable(self) -> None:
        candidates: list[dict[str, Any]] = []
        p = pair()
        p["requests"] = []
        candidates.append(p)
        p = pair()
        p["rejection_output"]["payload"]["call_id"] = "other"
        candidates.append(p)
        candidates += [
            pair('for(let i=0;i<2;i++) await tools.exec_command({cmd:"x"});'),
            pair('await tools.exec_command({cmd:"x"}); await tools.exec_command({cmd:"y"});'),
            pair('const cmd="x"; await tools.exec_command({cmd});'),
            pair('try { await tools.exec_command({cmd:"x"}); } catch(e) { throw e; }'),
        ]
        for p in candidates:
            with self.subTest(p=p):
                self.assertIsNone(supplement(self.audit([p]), 12)["corrected_tool_calls"])

    def test_canonical_overlap_is_unavailable_not_double_counted(self) -> None:
        for command in ["rm -f /tmp/test", "/bin/bash -lc 'rm -f /tmp/test'"]:
            r = supplement(
                self.audit(
                    canonical=[
                        {
                            "id": "i",
                            "type": "command_execution",
                            "command": command,
                            "status": "failed",
                        }
                    ]
                ),
                12,
            )
            self.assertIsNone(r["corrected_tool_calls"])

    def test_printed_source_is_not_runtime_rejection_and_no_code_executes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sessions").mkdir()
            (root / "events").write_text("")
            p = pair()
            p["rejection_output"]["payload"]["output"][0]["text"] = (
                "Script completed\nOutput:\nScript error:\n"
                "exec_command failed: CreateProcess Rejected(test)"
            )
            rows = [
                {"type": "response_item", "payload": p["requests"][0]["payload"]},
                {"type": "response_item", "payload": p["rejection_output"]["payload"]},
            ]
            (root / "sessions/s.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
            self.assertEqual(scan(root / "sessions", root / "events")["rejection_count"], 0)
            marker = root / "must-not-exist"
            source = (
                'require("fs").writeFileSync('
                + json.dumps(str(marker))
                + ',"bad"); throw new Error("exec_command failed: CreateProcess Rejected(test)");'
            )
            self.assertIsNone(supplement(self.audit([pair(source)]), 12)["corrected_tool_calls"])
            self.assertFalse(marker.exists())

    def test_missing_sessions_are_unavailable(self) -> None:
        audit = self.audit([])
        audit["session_files"] = 0
        self.assertIsNone(supplement(audit, 12)["corrected_tool_calls"])

    def test_success_envelope_cannot_forge_failed_runtime_result(self) -> None:
        p = pair()
        p["rejection_output"]["payload"]["output"][0]["text"] = (
            "Script completed\nWall time 0.0 seconds\nOutput:\n"
        )
        self.assertIsNone(supplement(self.audit([p]), 12)["corrected_tool_calls"])

    def test_other_failed_wrappers_need_proven_preexecution_syntax_rejection(self) -> None:
        p = pair("await tools.exec_command(")
        p["rejection_output"]["payload"]["output"][1]["text"] = (
            "Script error:\nSyntaxError: missing )"
        )
        audit = self.audit([])
        audit["other_failed_wrappers"] = [
            {"call_id": "c", "requests": p["requests"], "output": p["rejection_output"]}
        ]
        result = supplement(audit, 12)
        self.assertTrue(result["available"])
        self.assertEqual(result["corrected_tool_calls"], 12)
        p["requests"][0]["payload"]["input"] = 'await tools.exec_command({cmd:"x"});'
        self.assertIsNone(supplement(audit, 12)["corrected_tool_calls"])
        p["rejection_output"]["payload"]["output"][1]["text"] = (
            "Script error:\nTypeError: unknown failure"
        )
        self.assertIsNone(supplement(audit, 12)["corrected_tool_calls"])

    def test_unavailable_parser_does_not_fail_accounting(self) -> None:
        import subprocess
        from unittest.mock import patch

        for failure in [OSError("no Node"), subprocess.TimeoutExpired("node", 5)]:
            with patch(
                "clispecbench.agents.codex_rejected_tools.subprocess.run", side_effect=failure
            ):
                result = supplement(self.audit(), 12)
                self.assertIsNone(result["corrected_tool_calls"])
                self.assertTrue(result["problems"])

    def test_ambiguous_tool_count_preserves_all_token_fields(self) -> None:
        from clispecbench.agents.codex_rejected_tools import audit_result_tool_calls

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.json"
            usage = {
                "input_tokens": 100,
                "output_tokens": 30,
                "reasoning_output_tokens": 20,
                "tool_calls": 12,
                "tool_calls_definition": "underlying_tool_invocations_v2",
                "is_partial": False,
                "estimated_cost_usd": 0.5,
            }
            path.write_text(json.dumps({"metadata": {"run_uid": "test"}, "token_usage": usage}))
            original = path.read_bytes()
            audit = audit_result_tool_calls(path, 12)
            expected = dict(usage, tool_calls=None, tool_calls_definition=None)
            self.assertEqual(audit["corrected_token_usage"], expected)
            self.assertEqual(path.read_bytes(), original)


def test_truncated_session_makes_tool_count_unavailable(tmp_path: Path) -> None:
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    (sessions / "s.jsonl").write_text('{"type":"session_meta"}\n{"type":')
    events = tmp_path / "codex-events.jsonl"
    events.write_text('{"type":"turn.completed"}\n')
    evidence = scan(sessions, events)
    assert evidence["evidence_errors"]
    assert supplement(evidence, 2)["corrected_tool_calls"] is None


@pytest.mark.parametrize("bad_id", [[], {}, None, "", 7])
@pytest.mark.parametrize("location", ["session_request", "session_output", "canonical"])
def test_invalid_ids_only_invalidate_tool_metric(
    tmp_path: Path, bad_id: Any, location: str,
) -> None:
    from clispecbench.agents.codex_cli import CodexCLIAdapter

    sessions = tmp_path / "sessions"
    sessions.mkdir()
    event = {
        "type": "turn.completed",
        "usage": {"input_tokens": 100, "output_tokens": 20,
                  "cached_input_tokens": 30, "reasoning_output_tokens": 10},
    }
    logs = json.dumps(event) + "\n"
    if location == "canonical":
        session_record = {"type": "session_meta"}
        logs += json.dumps({"type": "item.completed", "item": {
            "type": "command_execution", "id": bad_id, "command": "true",
        }}) + "\n"
    else:
        kind = "function_call" if location == "session_request" else "function_call_output"
        session_record = {"type": "response_item", "payload": {
            "type": kind, "name": "exec", "call_id": bad_id, "arguments": "text(1)",
        }}
    (sessions / "s.jsonl").write_text(json.dumps(session_record) + "\n")
    events = tmp_path / "codex-events.jsonl"
    events.write_text(logs)
    evidence = scan(sessions, events)
    assert evidence["evidence_errors"]
    assert supplement(evidence, 1)["corrected_tool_calls"] is None
    adapter = CodexCLIAdapter(model="gpt-5.6-luna")
    usage = adapter.parse_token_usage(tmp_path, logs)
    assert usage is not None
    assert (usage.input_tokens, usage.output_tokens, usage.reasoning_output_tokens) == (100, 20, 10)
    assert usage.cache_read_input_tokens == 30
    assert usage.total_tokens == 120
    assert usage.tool_calls is None
    assert usage.tool_calls_definition is None
    assert not usage.is_partial
    assert adapter.estimate_cost(usage) == round((70 * 0.20 + 30 * 0.02 + 20 * 1.20) / 1e6, 6)


@pytest.mark.parametrize("failure", [OSError("evidence unreadable"), TypeError("bad shape")])
@pytest.mark.parametrize("stage", ["scan", "supplement"])
def test_evidence_reader_failure_preserves_authoritative_usage(
    tmp_path: Path, failure: Exception, stage: str,
) -> None:
    from clispecbench.agents.codex_cli import CodexCLIAdapter

    logs = json.dumps({"type": "turn.completed", "usage": {
        "input_tokens": 100, "output_tokens": 20, "cached_input_tokens": 30,
        "reasoning_output_tokens": 10,
    }})
    adapter = CodexCLIAdapter(model="gpt-5.6-luna")
    baseline = adapter.parse_token_usage(tmp_path, logs)
    assert baseline is not None
    with patch(f"clispecbench.agents.codex_cli.{stage}", side_effect=failure):
        usage = adapter.parse_token_usage(tmp_path, logs)
    assert usage is not None
    assert usage == baseline
    assert adapter.estimate_cost(usage) == adapter.estimate_cost(baseline)


@pytest.mark.parametrize("conflict_first", [False, True])
def test_conflicting_duplicate_other_failure_is_unavailable(conflict_first: bool) -> None:
    p = pair("await tools.exec_command(")
    p["rejection_output"]["payload"]["output"][1]["text"] = (
        "Script error:\nSyntaxError: missing )"
    )
    failed: dict[str, Any] = {
        "call_id": "c", "requests": p["requests"], "output": p["rejection_output"],
    }
    conflict = copy.deepcopy(failed)
    conflict["output"]["payload"]["output"][1]["text"] = (
        "Script error:\nTypeError: uncertain runtime failure"
    )
    audit = CountingTests().audit([])
    audit["other_failed_wrappers"] = [conflict, failed] if conflict_first else [failed, conflict]
    result = supplement(audit, 12)
    assert result["corrected_tool_calls"] is None
    assert any("conflicting duplicate failed wrapper" in p for p in result["problems"])


def test_identical_duplicate_other_failure_is_counted_once() -> None:
    p = pair("await tools.exec_command(")
    p["rejection_output"]["payload"]["output"][1]["text"] = (
        "Script error:\nSyntaxError: missing )"
    )
    failed: dict[str, Any] = {
        "call_id": "c", "requests": p["requests"], "output": p["rejection_output"],
    }
    duplicate = copy.deepcopy(failed)
    duplicate["output"]["path"] = "copied-session"
    audit = CountingTests().audit([])
    audit["other_failed_wrappers"] = [failed, duplicate]
    result = supplement(audit, 12)
    assert result["corrected_tool_calls"] == 12
    assert result["confirmed_preexecution_syntax_rejections"] == ["c"]


@pytest.mark.parametrize("location", ["sessions/s.jsonl", "codex-events.jsonl"])
def test_invalid_utf8_evidence_preserves_completed_turn_totals(
    tmp_path: Path, location: str,
) -> None:
    from clispecbench.agents.codex_cli import CodexCLIAdapter

    logs = json.dumps({"type": "turn.completed", "usage": {
        "input_tokens": 100, "output_tokens": 20, "cached_input_tokens": 30,
        "reasoning_output_tokens": 10,
    }})
    (tmp_path / "sessions").mkdir()
    (tmp_path / "sessions/s.jsonl").write_text('{"type":"session_meta"}\n')
    (tmp_path / "codex-events.jsonl").write_text(logs)
    (tmp_path / location).write_bytes(b"\xff")
    usage = CodexCLIAdapter().parse_token_usage(tmp_path, logs)
    assert usage is not None
    assert usage.total_tokens == 120
    assert usage.reasoning_output_tokens == 10
    assert usage.cache_read_input_tokens == 30
    assert usage.tool_calls is None
    assert usage.source == "codex_exec_turn_completed"
    assert not usage.is_partial
