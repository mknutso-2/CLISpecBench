from __future__ import annotations

from pathlib import Path

import pytest

from rs274_support import run_rs274

StateCase = tuple[str, str, float, float, str]

STATE_CASES: list[StateCase] = [
    (
        "tracks-latest-feed-rate",
        "F12.5\nF30.0\n",
        30.0,
        0.0,
        "OFF",
    ),
    (
        "tracks-spindle-speed-and-direction",
        "S1200\nM3\n",
        0.0,
        1200.0,
        "CW",
    ),
    (
        "tracks-spindle-stop-with-latest-speed",
        "S900\nM4\nS1500\nM5\n",
        0.0,
        1500.0,
        "OFF",
    ),
    (
        "tracks-feed-and-spindle-state-from-parameter-values",
        "#1=250.0\n#2=1200.0\n#3=3\nF#1\nS#2\nM#3\n",
        250.0,
        1200.0,
        "CW",
    ),
    (
        "tracks-feed-and-spindle-state-from-expressions",
        "F[500/2]\nS[600*2]\nM[1+2]\n",
        250.0,
        1200.0,
        "CW",
    ),
    (
        "tracks-feed-and-spindle-state-from-repeated-parameters-and-unary-ops",
        "#1=2\n#2=250.0\nF##1\nSABS[-1200.0]\nMABS[-3]\n",
        250.0,
        1200.0,
        "CW",
    ),
]


#
# See RS274/prompt/docs/RS274NGC.md section 3.3.2 "Words": a word is a
# letter followed by a real value. Sections 3.3.2.2 and 3.3.2.3 define
# parameter values and expressions as real values, so the supported F, S, and
# M words should accept those forms as well as numeric literals. Section
# 3.3.2.2 also explicitly allows repeated `#`, and section 3.3.2.4 defines
# unary-operation values as real values.
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
    submission_command: tuple[str, ...],
    input_gcode: str,
    expected_feed_rate: float,
    expected_spindle_speed: float,
    expected_spindle_direction: str,
    tmp_path: Path,
) -> None:
    completed, payload = run_rs274(
        submission_command,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload.get("error") is None
    assert payload.get("feed_rate") == expected_feed_rate
    assert payload.get("spindle_speed") == expected_spindle_speed
    assert payload.get("spindle_direction") == expected_spindle_direction
