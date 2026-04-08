"""Tests for the scoring pipeline."""
# pyright: reportUnknownMemberType=false

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from swe_buildbench.harness.results import TestOutcome, TestSummary
from swe_buildbench.harness.scoring import (
    compute_correctness,
    compute_subscores,
    compute_task_score,
    parse_json_report,
    run_hidden_tests,
)


def _outcome(node_id: str, outcome: str) -> TestOutcome:
    return TestOutcome(node_id=node_id, outcome=outcome, duration_seconds=0.0)


class TestComputeSubscores:
    """Per-capability breakdown derived from test file names."""

    def test_empty_test_list_yields_empty_dict(self) -> None:
        assert compute_subscores([]) == {}

    def test_groups_by_test_file_and_stores_passed_and_total(self) -> None:
        tests = [
            _outcome("tests/test_canned_cycles.py::test_g81", "passed"),
            _outcome("tests/test_canned_cycles.py::test_g82", "passed"),
            _outcome("tests/test_canned_cycles.py::test_g83", "failed"),
            _outcome("tests/test_g92_offsets.py::test_basic", "passed"),
            _outcome("tests/test_g92_offsets.py::test_reset", "failed"),
        ]
        scores = compute_subscores(tests)
        assert scores["subscore.canned_cycles.passed"] == 2.0
        assert scores["subscore.canned_cycles.total"] == 3.0
        assert scores["subscore.g92_offsets.passed"] == 1.0
        assert scores["subscore.g92_offsets.total"] == 2.0

    def test_failed_ratio_is_visible_as_zero_over_total(self) -> None:
        """The point of storing numerator+denominator: 0/28 is diagnostic,
        0.000 is not."""
        tests = [
            _outcome(f"tests/test_cutter_radius_compensation.py::t{i}", "failed")
            for i in range(28)
        ]
        scores = compute_subscores(tests)
        assert scores["subscore.cutter_radius_compensation.passed"] == 0.0
        assert scores["subscore.cutter_radius_compensation.total"] == 28.0

    def test_skipped_and_errored_count_toward_total_not_passed(self) -> None:
        tests = [
            _outcome("tests/test_probing.py::t1", "passed"),
            _outcome("tests/test_probing.py::t2", "skipped"),
            _outcome("tests/test_probing.py::t3", "error"),
            _outcome("tests/test_probing.py::t4", "failed"),
        ]
        scores = compute_subscores(tests)
        assert scores["subscore.probing.passed"] == 1.0
        assert scores["subscore.probing.total"] == 4.0

    def test_build_bucket_is_excluded(self) -> None:
        """test_build.py is already reported via BuildResult — don't double-count."""
        tests = [
            _outcome("tests/test_build.py::test_builds", "passed"),
            _outcome("tests/test_canned_cycles.py::test_g81", "passed"),
        ]
        scores = compute_subscores(tests)
        assert not any(k.startswith("subscore.build.") for k in scores)
        assert "subscore.canned_cycles.passed" in scores

    def test_nonstandard_node_ids_are_skipped_not_crashed_on(self) -> None:
        """Node IDs that don't match ``test_<bucket>.py::...`` are silently
        dropped, not errored on — scoring must never throw."""
        tests = [
            _outcome("weird_thing", "passed"),
            _outcome("tests/notatest.py::t", "passed"),
            _outcome("tests/test_canned_cycles.py::test_g81", "passed"),
        ]
        scores = compute_subscores(tests)
        assert scores == {
            "subscore.canned_cycles.passed": 1.0,
            "subscore.canned_cycles.total": 1.0,
        }

    def test_bucket_keys_are_sorted(self) -> None:
        """Deterministic key order makes extension_scores diffs across runs
        readable in git / json."""
        tests = [
            _outcome("tests/test_zeta.py::t", "passed"),
            _outcome("tests/test_alpha.py::t", "passed"),
            _outcome("tests/test_mike.py::t", "passed"),
        ]
        keys = [k for k in compute_subscores(tests) if k.endswith(".passed")]
        assert keys == [
            "subscore.alpha.passed",
            "subscore.mike.passed",
            "subscore.zeta.passed",
        ]


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
