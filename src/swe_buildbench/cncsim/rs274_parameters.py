from __future__ import annotations

from typing import Final

G28_HOME_X_PARAMETER: Final = 5161
G28_HOME_Y_PARAMETER: Final = 5162
G28_HOME_Z_PARAMETER: Final = 5163
G28_HOME_PARAMETER_INDICES: Final = (
    G28_HOME_X_PARAMETER,
    G28_HOME_Y_PARAMETER,
    G28_HOME_Z_PARAMETER,
)

G30_HOME_X_PARAMETER: Final = 5181
G30_HOME_Y_PARAMETER: Final = 5182
G30_HOME_Z_PARAMETER: Final = 5183
G30_HOME_PARAMETER_INDICES: Final = (
    G30_HOME_X_PARAMETER,
    G30_HOME_Y_PARAMETER,
    G30_HOME_Z_PARAMETER,
)

G92_X_OFFSET_PARAMETER: Final = 5211
G92_Y_OFFSET_PARAMETER: Final = 5212
G92_Z_OFFSET_PARAMETER: Final = 5213
G92_OFFSET_PARAMETER_INDICES: Final = (
    G92_X_OFFSET_PARAMETER,
    G92_Y_OFFSET_PARAMETER,
    G92_Z_OFFSET_PARAMETER,
)

SELECTED_COORDINATE_SYSTEM_PARAMETER: Final = 5220
COORDINATE_SYSTEM_1_X_PARAMETER: Final = 5221


def coordinate_system_axis_parameter(system_number: int, axis_index: int) -> int:
    if system_number < 1 or system_number > 9:
        raise ValueError("system_number must be from 1 to 9")
    if axis_index < 0 or axis_index > 2:
        raise ValueError("axis_index must be 0, 1, or 2")

    return COORDINATE_SYSTEM_1_X_PARAMETER + ((system_number - 1) * 20) + axis_index


def coordinate_system_xyz_parameter_indices(system_number: int) -> tuple[int, int, int]:
    x_parameter = coordinate_system_axis_parameter(system_number, 0)
    return (x_parameter, x_parameter + 1, x_parameter + 2)


required_non_rotational_parameter_indices = [
    *G28_HOME_PARAMETER_INDICES,
    *G30_HOME_PARAMETER_INDICES,
    *G92_OFFSET_PARAMETER_INDICES,
    SELECTED_COORDINATE_SYSTEM_PARAMETER,
]
for coordinate_system_number in range(1, 10):
    required_non_rotational_parameter_indices.extend(
        coordinate_system_xyz_parameter_indices(coordinate_system_number)
    )

REQUIRED_NON_ROTATIONAL_PARAMETER_INDICES: Final = tuple(required_non_rotational_parameter_indices)
