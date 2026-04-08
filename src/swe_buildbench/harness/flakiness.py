"""Cross-run flakiness analysis.

Given multiple runs of the *same* (task, agent, model, eval), identify
tests whose outcomes aren't unanimous. This is diagnostic, not scored —
it tells you which tests are unreliable signals when comparing agents,
and which capabilities an agent passes by luck vs. by understanding.

The module is a pure function of ``RunResult`` objects: no I/O, no
storage. Flakiness is computed on demand by ``swe-buildbench results
--flakiness``.
"""

from __future__ import annotations

from dataclasses import dataclass

from swe_buildbench.harness.results import RunResult

# Single-char codes for outcomes. Must be 1 character so the pattern
# reads as a compact string (e.g. "PFP" across 3 runs).
_OUTCOME_CHAR: dict[str, str] = {
    "passed": "P",
    "failed": "F",
    "skipped": "S",
    "error": "E",
}
# Used when a test is present in some runs of a group but not others —
# e.g. a new test was added between runs, or a run errored out before
# collection.
_MISSING_CHAR = "."


@dataclass(frozen=True)
class FlakyTest:
    """A single test whose outcome isn't unanimous across a group."""

    node_id: str
    pattern: str  # One char per run in group order, e.g. "PFP".


@dataclass(frozen=True)
class FlakinessReport:
    """Flakiness summary for a single group of same-key runs."""

    total_tests: int  # Union of all node_ids seen in the group.
    flaky: list[FlakyTest]

    @property
    def stable_count(self) -> int:
        return self.total_tests - len(self.flaky)


def _outcome_char(outcome: str) -> str:
    return _OUTCOME_CHAR.get(outcome, "?")


def compute_flakiness(runs: list[RunResult]) -> FlakinessReport:
    """Return per-test outcome patterns for tests that flipped across *runs*.

    *runs* must all share the same (task, agent, model, eval); callers are
    responsible for grouping. With fewer than 2 runs, flakiness is
    undefined and an empty report is returned — there's nothing to
    compare against.

    A test is "flaky" iff its outcome is not unanimous across the runs it
    appears in. Tests missing from a run (e.g. a test added between runs)
    get ``.`` for that run's slot; if a test appears in only one run, it
    cannot flip and is therefore *not* flaky.
    """
    if len(runs) < 2:
        return FlakinessReport(total_tests=0, flaky=[])

    # node_id -> list of outcome chars, one per run, "." if not present
    per_test: dict[str, list[str]] = {}
    for run_idx, run in enumerate(runs):
        seen_this_run: set[str] = set()
        for t in run.tests:
            if t.node_id not in per_test:
                per_test[t.node_id] = [_MISSING_CHAR] * len(runs)
            per_test[t.node_id][run_idx] = _outcome_char(t.outcome)
            seen_this_run.add(t.node_id)
        # Tests seen in earlier runs but not this one already have "." —
        # nothing to do.

    flaky: list[FlakyTest] = []
    for node_id in sorted(per_test):
        chars = per_test[node_id]
        # Ignore "." when deciding unanimity: a test that passed in run1
        # and was missing in run2 is not "flaky," it's "absent from run2."
        real = [c for c in chars if c != _MISSING_CHAR]
        if len(real) < 2:
            continue
        if len(set(real)) == 1:
            continue
        flaky.append(FlakyTest(node_id=node_id, pattern="".join(chars)))

    return FlakinessReport(total_tests=len(per_test), flaky=flaky)
