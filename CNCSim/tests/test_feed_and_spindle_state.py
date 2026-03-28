from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.test_support import run_cncsim

StateCase = tuple[str, str, float, float, str]

STATE_CASES: list[StateCase] = [
    (
        "tracks-latest-feed-rate",
        "F12.5\n"
        "F30.0\n",
        30.0,
        0.0,
        "OFF",
    ),
    (
        "tracks-spindle-speed-and-direction",
        "S1200\n"
        "M3\n",
        0.0,
        1200.0,
        "CW",
    ),
    (
        "tracks-spindle-stop-with-latest-speed",
        "S900\n"
        "M4\n"
        "S1500\n"
        "M5\n",
        0.0,
        1500.0,
        "OFF",
    ),
]


@pytest.mark.parametrize(
    ("input_gcode", "expected_feed_rate", "expected_spindle_speed", "expected_spindle_direction"),
    [
        (
            input_gcode,
            expected_feed_rate,
            expected_spindle_speed,
            expected_spindle_direction,
        )
        for (
            _,
            input_gcode,
            expected_feed_rate,
            expected_spindle_speed,
            expected_spindle_direction,
        ) in STATE_CASES
    ],
    ids=[case_id for case_id, _, _, _, _ in STATE_CASES],
)
def test_application_tracks_feed_and_spindle_state(
    built_executable_path: Path,
    input_gcode: str,
    expected_feed_rate: float,
    expected_spindle_speed: float,
    expected_spindle_direction: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["feed_rate"] == expected_feed_rate
    assert payload["spindle_speed"] == expected_spindle_speed
    assert payload["spindle_direction"] == expected_spindle_direction
