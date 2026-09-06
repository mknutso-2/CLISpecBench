"""Back-boring regression cases grounded in RS274 section 3.5.16.8."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from rs274_support import (
    input_line,
    mapping_field,
    reconstruct_state,
    run_rs274,
    run_rs274_trace,
    trace_entries,
)


def assert_close(value: object, expected: float, *, abs_tol: float) -> None:
    assert isinstance(value, int | float)
    assert math.isclose(value, expected, rel_tol=1e-9, abs_tol=abs_tol), (
        f"Expected {expected}, got {value}"
    )


def test_g87_accepts_omitted_clearance_and_counterbore_words(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Clarifications.md supplies zero I/J/K; section 3.5.16 returns to clear Z.

    Keep a snapshot case so accepting omitted words does not depend on trace
    support. Feed, spindle direction, units, plane, and retract mode are explicit.
    """
    completed, payload = run_rs274(
        submission_command,
        input_gcode="G17 G20 G90 G98 M3 S100\nG0 X0 Y0 Z2\nG87 X1 Z-1 R0 F60\n",
        tmp_path=tmp_path,
    )
    assert completed.returncode == 0, completed.stderr
    position = mapping_field(payload, "machine_position")
    assert_close(position.get("z"), 2.0, abs_tol=1e-9)


@pytest.mark.trace
def test_g87_explicit_clearance_and_counterbore_path(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Section 3.5.16.8 steps 1–11 define the complete back-boring path.

    Nonzero I/J distinguish clearance from the hole center, and K differs from
    R so a simplified feed-to-R implementation cannot pass. The coarse distance
    step yields one endpoint per sub-motion under the trace contract; expected
    positions below are the explicit numbered spec motions, not reference output.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=(
            "G17 G20 G90 G98 M3 S100\nG0 X0 Y0 Z2\nG87 X1 Y2 Z-1 R0 I0.25 J0.5 K0.5 F60\n"
        ),
        trace_distance_step=1000.0,
        tmp_path=tmp_path,
    )
    entries = trace_entries(trace)
    cycle_indices = [
        i for i, entry in enumerate(entries) if entry.get("line_number") == input_line(3)
    ]
    expected = [
        ("rapid", (1.0, 2.0, 2.0)),  # Preliminary traverse to hole XY.
        ("rapid", (1.0, 2.0, 0.0)),  # Preliminary traverse to R.
        ("rapid", (1.25, 2.5, 0.0)),  # Step 1: I/J insertion clearance.
        ("rapid", (1.25, 2.5, -1.0)),  # Step 3: insert at Z depth.
        ("rapid", (1.0, 2.0, -1.0)),  # Step 4: center the tool in the hole.
        ("feed", (1.0, 2.0, 0.5)),  # Step 6: bore upward to K.
        ("feed", (1.0, 2.0, -1.0)),  # Step 7: feed back down to Z.
        ("rapid", (1.25, 2.5, -1.0)),  # Step 9: return to removal clearance.
        ("rapid", (1.25, 2.5, 2.0)),  # Step 10: withdraw to G98 clear Z.
        ("rapid", (1.0, 2.0, 2.0)),  # Step 11: return to hole XY.
    ]
    assert len(cycle_indices) == len(expected)
    for entry_index, (kind, xyz) in zip(cycle_indices, expected, strict=True):
        assert entries[entry_index].get("motion_kind") == kind
        position = mapping_field(reconstruct_state(trace, entry_index), "machine_position")
        for axis, value in zip(("x", "y", "z"), xyz, strict=True):
            assert_close(position.get(axis), value, abs_tol=1e-9)


@pytest.mark.trace
def test_g87_incremental_k_is_relative_to_resolved_depth(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Section 3.5.16.8 makes G91 K an increment from Z, not R or old Z.

    The initial and R planes both equal 2, so no incremental-R interpretation is
    involved. Resolved Z is -1 and K1.5 names +0.5; only the upward feed endpoint
    is checked here. The complete return/clearance path has its own test above.
    """
    _, _, trace = run_rs274_trace(
        submission_command,
        input_gcode=(
            "G17 G20 G90 G98 M3 S100\nG0 X0 Y0 Z2\nG91 G87 X1 Y2 Z-3 R0 I0.25 J0.5 K1.5 F60\n"
        ),
        trace_distance_step=1000.0,
        tmp_path=tmp_path,
    )
    feed_indices = [
        i
        for i, entry in enumerate(trace_entries(trace))
        if entry.get("line_number") == input_line(3) and entry.get("motion_kind") == "feed"
    ]
    assert feed_indices, "G87 must emit the upward boring feed"
    position = mapping_field(reconstruct_state(trace, feed_indices[0]), "machine_position")
    assert_close(position.get("z"), 0.5, abs_tol=1e-9)
