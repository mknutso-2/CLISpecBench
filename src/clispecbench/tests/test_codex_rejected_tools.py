import copy
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

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
