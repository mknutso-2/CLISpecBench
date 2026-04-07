from __future__ import annotations

from pathlib import Path

import pytest

from cncsim_support import run_cncsim, with_default_rotary_axes
from modal_groups import GCODE_MODAL_GROUP_FEED_RATE_MODE

FeedRateModeCase = tuple[str, str, str, float, dict[str, float]]

ZERO_OFFSET_P1_SETUP = "G10 L2 P1 X0.0 Y0.0 Z0.0 A0.0 B0.0 C0.0\nG54\n"

FEED_RATE_MODE_CASES: list[FeedRateModeCase] = [
    (
        "g93-accepts-g1-motion-with-f",
        ZERO_OFFSET_P1_SETUP + "G90\n" + "G93\n" + "G1 X1.0 F2.0\n",
        "G93",
        2.0,
        {"x": 1.0, "y": 0.0, "z": 0.0},
    ),
    (
        "g93-does-not-affect-g0-motions",
        ZERO_OFFSET_P1_SETUP + "G90\n" + "G93\n" + "G0 X1.0\n",
        "G93",
        0.0,
        {"x": 1.0, "y": 0.0, "z": 0.0},
    ),
    (
        "g93-accepts-g2-motion-with-f",
        ZERO_OFFSET_P1_SETUP
        + "G17\n"
        + "G90\n"
        + "G0 X1.0 Y0.0 Z5.0\n"
        + "G93\n"
        + "G2 X0.0 Y-1.0 Z4.0 I-1.0 J0.0 F2.0\n",
        "G93",
        2.0,
        {"x": 0.0, "y": -1.0, "z": 4.0},
    ),
    (
        "g94-restores-units-per-minute-mode-after-g93",
        ZERO_OFFSET_P1_SETUP
        + "G90\n"
        + "G93\n"
        + "G1 X1.0 F2.0\n"
        + "G94\n"
        + "G1 X2.0\n",
        "G94",
        2.0,
        {"x": 2.0, "y": 0.0, "z": 0.0},
    ),
]


# RS274 section 3.5.19 defines the two feed-rate modes. Under G93, G1/G2/G3
# motion with an F word is valid, while G0 is unaffected. Switching back to G94
# restores units-per-minute mode, so the prior feed rate remains usable without
# repeating F on every subsequent G1 line.
@pytest.mark.parametrize(
    ("input_gcode", "expected_active_mode", "expected_feed_rate", "expected_machine_position"),
    [
        (
            input_gcode,
            expected_active_mode,
            expected_feed_rate,
            expected_machine_position,
        )
        for (
            _,
            input_gcode,
            expected_active_mode,
            expected_feed_rate,
            expected_machine_position,
        ) in FEED_RATE_MODE_CASES
    ],
    ids=[case_id for case_id, _, _, _, _ in FEED_RATE_MODE_CASES],
)
def test_application_tracks_feed_rate_mode_behavior(
    submission_command: tuple[str, ...],
    input_gcode: str,
    expected_active_mode: str,
    expected_feed_rate: float,
    expected_machine_position: dict[str, float],
    tmp_path: Path,
) -> None:
    completed, payload = run_cncsim(
        submission_command,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )

    assert completed.returncode == 0, completed.stderr
    assert payload["error"] is None
    assert payload["active_modal_g_codes"][GCODE_MODAL_GROUP_FEED_RATE_MODE] == expected_active_mode
    assert payload["feed_rate"] == expected_feed_rate
    assert payload["machine_position"] == with_default_rotary_axes(expected_machine_position)
