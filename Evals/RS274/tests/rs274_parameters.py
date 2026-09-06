from __future__ import annotations

from typing import Final

G28_HOME_X_PARAMETER: Final = 5161
G28_HOME_Y_PARAMETER: Final = 5162
G28_HOME_Z_PARAMETER: Final = 5163
G28_HOME_A_PARAMETER: Final = 5164
G28_HOME_B_PARAMETER: Final = 5165
G28_HOME_C_PARAMETER: Final = 5166
G28_HOME_PARAMETER_INDICES: Final = (
    G28_HOME_X_PARAMETER,
    G28_HOME_Y_PARAMETER,
    G28_HOME_Z_PARAMETER,
    G28_HOME_A_PARAMETER,
    G28_HOME_B_PARAMETER,
    G28_HOME_C_PARAMETER,
)
G28_HOME_XYZ_PARAMETER_INDICES: Final = G28_HOME_PARAMETER_INDICES[:3]

G30_HOME_X_PARAMETER: Final = 5181
G30_HOME_Y_PARAMETER: Final = 5182
G30_HOME_Z_PARAMETER: Final = 5183
G30_HOME_A_PARAMETER: Final = 5184
G30_HOME_B_PARAMETER: Final = 5185
G30_HOME_C_PARAMETER: Final = 5186
G30_HOME_PARAMETER_INDICES: Final = (
    G30_HOME_X_PARAMETER,
    G30_HOME_Y_PARAMETER,
    G30_HOME_Z_PARAMETER,
    G30_HOME_A_PARAMETER,
    G30_HOME_B_PARAMETER,
    G30_HOME_C_PARAMETER,
)
G30_HOME_XYZ_PARAMETER_INDICES: Final = G30_HOME_PARAMETER_INDICES[:3]

PROBE_TRIP_X_PARAMETER: Final = 5061
PROBE_TRIP_Y_PARAMETER: Final = 5062
PROBE_TRIP_Z_PARAMETER: Final = 5063
PROBE_TRIP_A_PARAMETER: Final = 5064
PROBE_TRIP_B_PARAMETER: Final = 5065
PROBE_TRIP_C_PARAMETER: Final = 5066
PROBE_TRIP_PARAMETER_INDICES: Final = (
    PROBE_TRIP_X_PARAMETER,
    PROBE_TRIP_Y_PARAMETER,
    PROBE_TRIP_Z_PARAMETER,
    PROBE_TRIP_A_PARAMETER,
    PROBE_TRIP_B_PARAMETER,
    PROBE_TRIP_C_PARAMETER,
)

G92_X_OFFSET_PARAMETER: Final = 5211
G92_Y_OFFSET_PARAMETER: Final = 5212
G92_Z_OFFSET_PARAMETER: Final = 5213
G92_A_OFFSET_PARAMETER: Final = 5214
G92_B_OFFSET_PARAMETER: Final = 5215
G92_C_OFFSET_PARAMETER: Final = 5216
G92_OFFSET_PARAMETER_INDICES: Final = (
    G92_X_OFFSET_PARAMETER,
    G92_Y_OFFSET_PARAMETER,
    G92_Z_OFFSET_PARAMETER,
    G92_A_OFFSET_PARAMETER,
    G92_B_OFFSET_PARAMETER,
    G92_C_OFFSET_PARAMETER,
)
G92_XYZ_OFFSET_PARAMETER_INDICES: Final = G92_OFFSET_PARAMETER_INDICES[:3]

SELECTED_COORDINATE_SYSTEM_PARAMETER: Final = 5220
COORDINATE_SYSTEM_1_X_PARAMETER: Final = 5221


def coordinate_system_axis_parameter(system_number: int, axis_index: int) -> int:
    if system_number < 1 or system_number > 9:
        raise ValueError("system_number must be from 1 to 9")
    if axis_index < 0 or axis_index > 5:
        raise ValueError("axis_index must be 0 through 5")

    return COORDINATE_SYSTEM_1_X_PARAMETER + ((system_number - 1) * 20) + axis_index


def coordinate_system_xyz_parameter_indices(system_number: int) -> tuple[int, int, int]:
    x_parameter = coordinate_system_axis_parameter(system_number, 0)
    return (x_parameter, x_parameter + 1, x_parameter + 2)


def coordinate_system_xyzabc_parameter_indices(
    system_number: int,
) -> tuple[int, int, int, int, int, int]:
    x_parameter = coordinate_system_axis_parameter(system_number, 0)
    return (
        x_parameter,
        x_parameter + 1,
        x_parameter + 2,
        x_parameter + 3,
        x_parameter + 4,
        x_parameter + 5,
    )


# RS274 section 3.2.1 and Table 2 require every entry for each supported axis.
# Rotary entries may be omitted only for unused axes; this eval uses A/B/C.
required_parameter_indices = [
    *G28_HOME_PARAMETER_INDICES,
    *G30_HOME_PARAMETER_INDICES,
    *G92_OFFSET_PARAMETER_INDICES,
    SELECTED_COORDINATE_SYSTEM_PARAMETER,
]
for coordinate_system_number in range(1, 10):
    required_parameter_indices.extend(
        coordinate_system_xyzabc_parameter_indices(coordinate_system_number)
    )

REQUIRED_PARAMETER_INDICES: Final = tuple(required_parameter_indices)
