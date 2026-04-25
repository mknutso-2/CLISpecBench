from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import pytest

from .conftest import run_las
from .las_support import (
    canonical_dataset,
    dataset_for_point_format,
    dataset_with_external_waveform_packets,
    dataset_with_legacy_multi_returns,
    dataset_with_modern_multi_returns,
    dataset_without_waveform_packets,
    encode_dataset,
    encode_request_for_inspect,
    encode_request_for_render,
    payload_dataset,
    payload_las_bytes,
)

EXACT_RENDER_FORMATS = [6, 7, 8, 9, 10]
LEGACY_RENDER_FORMATS = [0, 1, 2, 3, 4, 5]


def _legacy_counter_pair_from_bytes(data: bytes) -> tuple[int, list[int]]:
    count = int.from_bytes(data[107:111], "little")
    returns = [
        int.from_bytes(data[111 + (index * 4) : 115 + (index * 4)], "little") for index in range(5)
    ]
    return count, returns


def _without_legacy_counter_pair(data: bytes) -> bytes:
    normalized = bytearray(data)
    normalized[107:131] = b"\x00" * 24
    return bytes(normalized)


def _populated_legacy_returns(points: list[dict[str, Any]]) -> list[int]:
    returns = [0, 0, 0, 0, 0]
    for point in points:
        return_number = cast(int, point["return_number"])
        if 1 <= return_number <= 5:
            returns[return_number - 1] += 1
    return returns


# Public-header fields whose stored value does not depend on the chosen point
# format — testing them once on a representative format is enough; running
# all 11 formats would fail 11 times for the same parser bug.
_HEADER_FORMAT_INVARIANT_FIELDS = (
    "file_source_id",
    "project_id",
    "version_major",
    "version_minor",
    "system_identifier",
    "generating_software",
    "file_creation_day_of_year",
    "file_creation_year",
    "header_size",
    "x_scale_factor",
    "y_scale_factor",
    "z_scale_factor",
    "x_offset",
    "y_offset",
    "z_offset",
)
# Public-header fields whose value or interpretation legitimately depends on
# the point format (legacy vs modern counters, waveform-only offsets, the
# format byte itself, extents that vary with `point_for_format(...)`).
_HEADER_FORMAT_LAYOUT_FIELDS = (
    "global_encoding",
    "point_data_record_format",
    "point_data_record_length",
    "offset_to_point_data",
    "number_of_variable_length_records",
    "number_of_extended_variable_length_records",
    "start_of_first_extended_variable_length_record",
    "start_of_waveform_data_packet_record",
)
_HEADER_COUNTER_FIELDS = (
    "legacy_number_of_point_records",
    "legacy_number_of_points_by_return",
    "number_of_point_records",
    "number_of_points_by_return",
)
_HEADER_EXTENT_FIELDS = (
    "max_x",
    "min_x",
    "max_y",
    "min_y",
    "max_z",
    "min_z",
)


def _inspect_header(
    submission_command: Sequence[str], tmp_path: Path, point_format: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    dataset = dataset_for_point_format(point_format)
    _, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)
    assert payload is not None
    actual = cast(dict[str, Any], payload_dataset(payload)["header"])
    expected = cast(dict[str, Any], canonical_dataset(dataset)["header"])
    return actual, expected


@pytest.mark.parametrize("field", _HEADER_FORMAT_INVARIANT_FIELDS)
def test_inspect_header_format_invariant_field(
    submission_command: Sequence[str],
    tmp_path: Path,
    field: str,
) -> None:
    """Parametrize by *field* (not by format) so a single misread offset for
    `system_identifier` fails one named test, not 11 copies of the same fact.
    Format 6 is representative for the format-invariant fields tested here."""

    actual, expected = _inspect_header(submission_command, tmp_path, 6)
    assert actual[field] == expected[field]


@pytest.mark.parametrize("point_format", list(range(11)))
def test_inspect_header_format_layout_fields(
    submission_command: Sequence[str],
    tmp_path: Path,
    point_format: int,
) -> None:
    actual, expected = _inspect_header(submission_command, tmp_path, point_format)
    for field in _HEADER_FORMAT_LAYOUT_FIELDS:
        assert actual[field] == expected[field], field


@pytest.mark.parametrize("point_format", list(range(11)))
def test_inspect_header_counter_fields(
    submission_command: Sequence[str],
    tmp_path: Path,
    point_format: int,
) -> None:
    actual, expected = _inspect_header(submission_command, tmp_path, point_format)
    for field in _HEADER_COUNTER_FIELDS:
        assert actual[field] == expected[field], field


@pytest.mark.parametrize("point_format", list(range(11)))
def test_inspect_header_extent_fields(
    submission_command: Sequence[str],
    tmp_path: Path,
    point_format: int,
) -> None:
    actual, expected = _inspect_header(submission_command, tmp_path, point_format)
    for field in _HEADER_EXTENT_FIELDS:
        assert actual[field] == expected[field], field


@pytest.mark.parametrize("point_format", list(range(11)))
def test_inspect_point_format_point_payload(
    submission_command: Sequence[str],
    tmp_path: Path,
    point_format: int,
) -> None:
    dataset = dataset_for_point_format(point_format)
    _, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)

    assert payload is not None
    actual = payload_dataset(payload)
    expected = canonical_dataset(dataset)
    assert actual["points"] == expected["points"]


@pytest.mark.parametrize("point_format", list(range(11)))
def test_inspect_point_format_vlrs(
    submission_command: Sequence[str],
    tmp_path: Path,
    point_format: int,
) -> None:
    dataset = dataset_for_point_format(point_format)
    _, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)

    assert payload is not None
    actual = payload_dataset(payload)
    expected = canonical_dataset(dataset)
    assert actual["vlrs"] == expected["vlrs"]


@pytest.mark.parametrize("point_format", list(range(11)))
def test_inspect_point_format_evlrs(
    submission_command: Sequence[str],
    tmp_path: Path,
    point_format: int,
) -> None:
    dataset = dataset_for_point_format(point_format)
    _, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)

    assert payload is not None
    actual = payload_dataset(payload)
    expected = canonical_dataset(dataset)
    assert actual["evlrs"] == expected["evlrs"]


@pytest.mark.parametrize("point_format", EXACT_RENDER_FORMATS)
def test_render_exact_point_format_samples(
    submission_command: Sequence[str],
    tmp_path: Path,
    point_format: int,
) -> None:
    dataset = dataset_for_point_format(point_format)
    result, payload = run_las(
        submission_command,
        encode_request_for_render(dataset),
        tmp_path,
    )

    assert result.returncode == 0
    assert payload is not None
    assert payload["status"] == "ok"
    assert payload_las_bytes(payload) == encode_dataset(dataset)


@pytest.mark.parametrize("point_format", LEGACY_RENDER_FORMATS)
def test_render_legacy_formats_roundtrip_semantics(
    submission_command: Sequence[str],
    tmp_path: Path,
    point_format: int,
) -> None:
    dataset = dataset_for_point_format(point_format)
    render_result, render_payload = run_las(
        submission_command,
        encode_request_for_render(dataset),
        tmp_path,
    )

    assert render_result.returncode == 0
    assert render_payload is not None

    rendered = payload_las_bytes(render_payload)
    expected = encode_dataset(dataset)
    assert _without_legacy_counter_pair(rendered) == _without_legacy_counter_pair(expected)

    actual_count, actual_returns = _legacy_counter_pair_from_bytes(rendered)
    expected_points = cast(list[dict[str, Any]], dataset["points"])
    populated_count = len(expected_points)
    populated_returns = _populated_legacy_returns(expected_points)
    zeroed = actual_count == 0 and actual_returns == [0, 0, 0, 0, 0]
    populated = actual_count == populated_count and actual_returns == populated_returns
    assert zeroed or populated


def test_inspect_legacy_multi_return_counts(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_legacy_multi_returns()
    result, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)

    assert result.returncode == 0
    assert payload is not None
    assert cast(dict[str, Any], payload_dataset(payload)["header"])[
        "legacy_number_of_points_by_return"
    ] == [1, 1, 0, 0, 0]


def test_inspect_modern_multi_return_counts(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_modern_multi_returns()
    result, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)

    assert result.returncode == 0
    assert payload is not None
    assert cast(dict[str, Any], payload_dataset(payload)["header"])["number_of_points_by_return"][
        :4
    ] == [1, 1, 1, 0]


@pytest.mark.parametrize("point_format", [4, 5, 9, 10])
def test_waveform_capable_formats_accept_all_zero_waveform_blocks_without_descriptors(
    submission_command: Sequence[str],
    tmp_path: Path,
    point_format: int,
) -> None:
    dataset = dataset_without_waveform_packets(point_format)
    result, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)

    assert result.returncode == 0
    assert payload is not None
    assert payload_dataset(payload) == canonical_dataset(dataset)


def test_external_waveform_mode_does_not_require_waveform_evlr(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_external_waveform_packets()
    result, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)

    assert result.returncode == 0
    assert payload is not None
    assert payload_dataset(payload) == canonical_dataset(dataset)
