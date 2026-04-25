"""Tests for harness.flakiness — per-test outcome patterns across runs.

Each test name states the property it proves.
"""

from __future__ import annotations

from clispecbench.harness.flakiness import FlakyTest, compute_flakiness
from clispecbench.harness.results import (
    BuildResult,
    RunMetadata,
    RunResult,
    Scores,
    TestOutcome,
    TestSummary,
)


def _make_run(outcomes: dict[str, str]) -> RunResult:
    """Build a minimal RunResult with the given {node_id: outcome} tests."""
    tests = [
        TestOutcome(node_id=nid, outcome=o, duration_seconds=0.0) for nid, o in outcomes.items()
    ]
    summary = TestSummary()
    for t in tests:
        if t.outcome == "passed":
            summary.passed += 1
        elif t.outcome == "failed":
            summary.failed += 1
        elif t.outcome == "skipped":
            summary.skipped += 1
        else:
            summary.error += 1
    return RunResult(
        metadata=RunMetadata(
            run_uid="00000000-0000-0000-0000-000000000001",
            task="t",
            agent="a",
            agent_version="v",
            prompt_variant="base",
            run_number=1,
            timestamp="",
            test_suite_version="",
            eval_version="",
            harness_version="",
            docker_image_sha="",
            wall_clock_seconds=0.0,
            exit_reason="completed",
        ),
        token_usage=None,
        build=BuildResult(success=True, duration_seconds=0.0),
        tests=tests,
        test_summary=summary,
        scores=Scores(),
    )


def test_fewer_than_two_runs_is_empty_report() -> None:
    """Can't measure flakiness with 0 or 1 runs — not enough data to
    flip."""
    assert compute_flakiness([]).flaky == []
    single = compute_flakiness([_make_run({"t::a": "passed"})])
    assert single.flaky == []
    assert single.total_tests == 0  # nothing to compare


def test_all_unanimous_yields_no_flaky_tests() -> None:
    runs = [
        _make_run({"t::a": "passed", "t::b": "failed"}),
        _make_run({"t::a": "passed", "t::b": "failed"}),
        _make_run({"t::a": "passed", "t::b": "failed"}),
    ]
    report = compute_flakiness(runs)
    assert report.flaky == []
    assert report.total_tests == 2
    assert report.stable_count == 2


def test_flipping_test_surfaces_with_pattern() -> None:
    runs = [
        _make_run({"t::a": "passed"}),
        _make_run({"t::a": "failed"}),
        _make_run({"t::a": "passed"}),
    ]
    report = compute_flakiness(runs)
    assert report.flaky == [FlakyTest(node_id="t::a", pattern="PFP")]


def test_stable_and_flipping_tests_coexist() -> None:
    runs = [
        _make_run({"t::stable": "passed", "t::flaky": "passed"}),
        _make_run({"t::stable": "passed", "t::flaky": "failed"}),
    ]
    report = compute_flakiness(runs)
    assert [f.node_id for f in report.flaky] == ["t::flaky"]
    assert report.total_tests == 2
    assert report.stable_count == 1


def test_missing_from_one_run_is_not_flaky() -> None:
    """A test present in run1 + run2 but absent from run3 isn't 'flaky'
    — it's just missing. It should only be flagged if the outcomes it
    DID produce disagree."""
    runs = [
        _make_run({"t::a": "passed"}),
        _make_run({"t::a": "passed"}),
        _make_run({}),
    ]
    report = compute_flakiness(runs)
    assert report.flaky == []
    # But a test missing + disagreeing across the runs it IS in is flaky
    runs2 = [
        _make_run({"t::a": "passed"}),
        _make_run({"t::a": "failed"}),
        _make_run({}),
    ]
    report2 = compute_flakiness(runs2)
    assert len(report2.flaky) == 1
    assert report2.flaky[0].pattern == "PF."


def test_test_only_in_one_run_is_not_flaky() -> None:
    """A test that only appears in a single run can't flip — no data to
    compare it against."""
    runs = [
        _make_run({"t::only_in_r1": "failed"}),
        _make_run({"t::only_in_r2": "passed"}),
    ]
    report = compute_flakiness(runs)
    assert report.flaky == []
    # Both still count toward total_tests (observed at least once).
    assert report.total_tests == 2


def test_outcome_char_mapping_covers_all_four_states() -> None:
    runs = [
        _make_run(
            {
                "t::p": "passed",
                "t::f": "failed",
                "t::s": "skipped",
                "t::e": "error",
            }
        ),
        _make_run(
            {
                "t::p": "failed",
                "t::f": "passed",
                "t::s": "error",
                "t::e": "skipped",
            }
        ),
    ]
    report = compute_flakiness(runs)
    patterns = {f.node_id: f.pattern for f in report.flaky}
    assert patterns == {
        "t::p": "PF",
        "t::f": "FP",
        "t::s": "SE",
        "t::e": "ES",
    }


def test_flaky_list_is_sorted_by_node_id() -> None:
    runs = [
        _make_run({"t::zebra": "passed", "t::apple": "passed"}),
        _make_run({"t::zebra": "failed", "t::apple": "failed"}),
    ]
    report = compute_flakiness(runs)
    assert [f.node_id for f in report.flaky] == ["t::apple", "t::zebra"]
