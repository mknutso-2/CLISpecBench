from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.cncsim.modal_groups import (
    GCODE_MODAL_GROUP_COORDINATE_SYSTEM_SELECTION,
    GCODE_MODAL_GROUP_CUTTER_RADIUS_COMPENSATION,
    GCODE_MODAL_GROUP_DISTANCE_MODE,
    GCODE_MODAL_GROUP_FEED_RATE_MODE,
    GCODE_MODAL_GROUP_MOTION,
    GCODE_MODAL_GROUP_NON_MODAL,
    GCODE_MODAL_GROUP_PATH_CONTROL_MODE,
    GCODE_MODAL_GROUP_PLANE_SELECTION,
    GCODE_MODAL_GROUP_RETURN_MODE_IN_CANNED_CYCLES,
    GCODE_MODAL_GROUP_TOOL_LENGTH_OFFSET,
    GCODE_MODAL_GROUP_UNITS,
)
from swe_buildbench.cncsim.test_support import run_cncsim_invalid_input

GcodeGroupErrorCase = tuple[str, str, str]

GCODE_GROUP_ERROR_CASES: list[GcodeGroupErrorCase] = [
    (
        "non-modal-group",
        GCODE_MODAL_GROUP_NON_MODAL,
        "G10 G10 L2 P1 X0.0\n",
    ),
    (
        "motion-group",
        GCODE_MODAL_GROUP_MOTION,
        "G90 G0 G1 X1.0\n",
    ),
    (
        "plane-selection-group",
        GCODE_MODAL_GROUP_PLANE_SELECTION,
        "G17 G18\n",
    ),
    (
        "distance-mode-group",
        GCODE_MODAL_GROUP_DISTANCE_MODE,
        "G90 G91\n",
    ),
    (
        "feed-rate-mode-group",
        GCODE_MODAL_GROUP_FEED_RATE_MODE,
        "G93 G94\n",
    ),
    (
        "units-group",
        GCODE_MODAL_GROUP_UNITS,
        "G20 G21\n",
    ),
    (
        "cutter-radius-compensation-group",
        GCODE_MODAL_GROUP_CUTTER_RADIUS_COMPENSATION,
        "G40 G41\n",
    ),
    (
        "tool-length-offset-group",
        GCODE_MODAL_GROUP_TOOL_LENGTH_OFFSET,
        "G43 H1 G49\n",
    ),
    (
        "return-mode-group",
        GCODE_MODAL_GROUP_RETURN_MODE_IN_CANNED_CYCLES,
        "G98 G99\n",
    ),
    (
        "coordinate-system-selection-group",
        GCODE_MODAL_GROUP_COORDINATE_SYSTEM_SELECTION,
        "G54 G55\n",
    ),
    (
        "path-control-mode-group",
        GCODE_MODAL_GROUP_PATH_CONTROL_MODE,
        "G61 G64\n",
    ),
]


# See CNCSim/prompt/docs/RS274NGC.md section 3.3.5 "Item Repeats": a line may
# contain any number of G words, but two G words from the same group may not
# appear on the same line. These cases cover each supported G-code group.
@pytest.mark.parametrize(
    "input_gcode",
    [
        input_gcode
        for _, group_number, input_gcode in GCODE_GROUP_ERROR_CASES
    ],
    ids=[
        f"group-{group_number}-{case_id}"
        for case_id, group_number, _ in GCODE_GROUP_ERROR_CASES
    ],
)
def test_application_rejects_multiple_g_words_from_the_same_group(
    built_executable_path: Path,
    input_gcode: str,
    tmp_path: Path,
) -> None:
    run_cncsim_invalid_input(
        built_executable_path,
        input_gcode=input_gcode,
        tmp_path=tmp_path,
    )
