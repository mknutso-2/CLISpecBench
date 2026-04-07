"""Tests for the scoring pipeline."""
# pyright: reportUnknownMemberType=false

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from swe_buildbench.harness.results import TestSummary
from swe_buildbench.harness.scoring import (
    compute_correctness,
    compute_task_score,
    parse_json_report,
    run_hidden_tests,
)


class TestRunHiddenTests:
    """Verify that run_hidden_tests passes --implementation-root to pytest."""

    def test_passes_implementation_root_flag(self, tmp_path: Path) -> None:
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        submission_dir = tmp_path / "submission"
        submission_dir.mkdir()
        report_path = tmp_path / "report.json"

        # Write a minimal JSON report so parsing succeeds
        report_path.write_text(json.dumps({"tests": []}))

        with patch("swe_buildbench.harness.scoring.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            run_hidden_tests(
                test_dir=test_dir,
                submission_dir=submission_dir,
                report_path=report_path,
                use_docker=False,
            )

        cmd = mock_run.call_args[0][0]
        assert any(arg.startswith("--implementation-root=") for arg in cmd), (
            f"Expected --implementation-root in command: {cmd}"
        )
        assert not any(arg.startswith("--executable=") for arg in cmd), (
            f"Should not pass --executable: {cmd}"
        )

    def test_passes_language_flag_when_specified(self, tmp_path: Path) -> None:
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        submission_dir = tmp_path / "submission"
        submission_dir.mkdir()
        report_path = tmp_path / "report.json"
        report_path.write_text(json.dumps({"tests": []}))

        with patch("swe_buildbench.harness.scoring.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            run_hidden_tests(
                test_dir=test_dir,
                submission_dir=submission_dir,
                report_path=report_path,
                language="py",
                use_docker=False,
            )

        cmd = mock_run.call_args[0][0]
        assert "--language=py" in cmd, f"Expected --language=py in command: {cmd}"

    def test_omits_language_flag_for_default_cpp(self, tmp_path: Path) -> None:
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        submission_dir = tmp_path / "submission"
        submission_dir.mkdir()
        report_path = tmp_path / "report.json"
        report_path.write_text(json.dumps({"tests": []}))

        with patch("swe_buildbench.harness.scoring.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            run_hidden_tests(
                test_dir=test_dir,
                submission_dir=submission_dir,
                report_path=report_path,
                use_docker=False,
            )

        cmd = mock_run.call_args[0][0]
        # Default language is cpp; the plugin's default is also cpp, so we
        # don't need to pass anything explicitly. Either omitted entirely
        # or explicitly --language=cpp is acceptable.
        language_args = [arg for arg in cmd if arg.startswith("--language=")]
        if language_args:
            assert language_args == ["--language=cpp"]

    def test_does_not_pass_executable_flag(self, tmp_path: Path) -> None:
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        submission_dir = tmp_path / "submission"
        submission_dir.mkdir()
        report_path = tmp_path / "report.json"
        report_path.write_text(json.dumps({"tests": []}))

        with patch("swe_buildbench.harness.scoring.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            run_hidden_tests(
                test_dir=test_dir,
                submission_dir=submission_dir,
                report_path=report_path,
                use_docker=False,
            )

        cmd = mock_run.call_args[0][0]
        assert "--executable" not in " ".join(cmd)


class TestParseJsonReport:
    """Verify JSON report parsing."""

    def test_parses_passed_tests(self, tmp_path: Path) -> None:
        report = {
            "tests": [
                {"nodeid": "test_a", "outcome": "passed", "duration": 0.1},
                {"nodeid": "test_b", "outcome": "passed", "duration": 0.2},
            ]
        }
        report_path = tmp_path / "report.json"
        report_path.write_text(json.dumps(report))

        tests, summary = parse_json_report(report_path)
        assert len(tests) == 2
        assert summary.passed == 2
        assert summary.total == 2

    def test_parses_mixed_outcomes(self, tmp_path: Path) -> None:
        report = {
            "tests": [
                {"nodeid": "test_a", "outcome": "passed", "duration": 0.1},
                {
                    "nodeid": "test_b",
                    "outcome": "failed",
                    "duration": 0.2,
                    "call": {"longrepr": "AssertionError: expected 1"},
                },
                {"nodeid": "test_c", "outcome": "skipped", "duration": 0.0},
            ]
        }
        report_path = tmp_path / "report.json"
        report_path.write_text(json.dumps(report))

        tests, summary = parse_json_report(report_path)
        assert summary.passed == 1
        assert summary.failed == 1
        assert summary.skipped == 1
        assert summary.total == 3
        assert tests[1].message == "AssertionError: expected 1"

    def test_missing_report_returns_empty(self, tmp_path: Path) -> None:
        tests, summary = parse_json_report(tmp_path / "nonexistent.json")
        assert tests == []
        assert summary.total == 0


class TestComputeCorrectness:
    def test_all_passed(self) -> None:
        assert compute_correctness(TestSummary(passed=10)) == pytest.approx(1.0)

    def test_half_passed(self) -> None:
        assert compute_correctness(TestSummary(passed=5, failed=5)) == pytest.approx(0.5)

    def test_no_tests(self) -> None:
        assert compute_correctness(TestSummary()) == 0.0


class TestComputeTaskScore:
    def test_correctness_only(self) -> None:
        scores = compute_task_score(0.8, None, None)
        assert scores.correctness == pytest.approx(0.8)
        assert scores.task_score == pytest.approx(0.8)

    def test_all_dimensions(self) -> None:
        scores = compute_task_score(1.0, 0.5, 0.5)
        expected = 0.6 * 1.0 + 0.2 * 0.5 + 0.2 * 0.5
        assert scores.task_score == pytest.approx(expected)
