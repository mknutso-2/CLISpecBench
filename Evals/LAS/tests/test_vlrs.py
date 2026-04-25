from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import pytest

from .conftest import run_las
from .las_support import (
    canonical_dataset,
    dataset_for_point_format,
    dataset_with_classification_lookup,
    dataset_with_extra_bytes,
    dataset_with_extra_bytes_type,
    dataset_with_geotiff_triplet,
    dataset_with_multiple_evlrs,
    dataset_with_unknown_records,
    dataset_with_wkt_pair,
    encode_dataset,
    encode_request_for_inspect,
    encode_request_for_render,
    payload_dataset,
    payload_las_bytes,
    undocumented_extra_bytes_vlr,
)


def _vlrs_from(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], dataset["vlrs"])


def _evlrs_from(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], dataset["evlrs"])


def _points_from(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], dataset["points"])


def _padded_ascii(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("ascii")


def _vlr_payloads(data: bytes) -> list[tuple[str, int, bytes]]:
    count = int.from_bytes(data[100:104], "little")
    cursor = 375
    records: list[tuple[str, int, bytes]] = []
    for _ in range(count):
        user_id = _padded_ascii(data[cursor + 2 : cursor + 18])
        record_id = int.from_bytes(data[cursor + 18 : cursor + 20], "little")
        payload_length = int.from_bytes(data[cursor + 20 : cursor + 22], "little")
        payload_start = cursor + 54
        payload_end = payload_start + payload_length
        records.append((user_id, record_id, data[payload_start:payload_end]))
        cursor = payload_end
    return records


def _evlr_payloads(data: bytes) -> list[tuple[str, int, bytes]]:
    first_evlr_offset = int.from_bytes(data[235:243], "little")
    count = int.from_bytes(data[243:247], "little")
    if first_evlr_offset == 0:
        return []
    cursor = first_evlr_offset
    records: list[tuple[str, int, bytes]] = []
    for _ in range(count):
        user_id = _padded_ascii(data[cursor + 2 : cursor + 18])
        record_id = int.from_bytes(data[cursor + 18 : cursor + 20], "little")
        payload_length = int.from_bytes(data[cursor + 20 : cursor + 28], "little")
        payload_start = cursor + 60
        payload_end = payload_start + payload_length
        records.append((user_id, record_id, data[payload_start:payload_end]))
        cursor = payload_end
    return records


def test_inspect_geotiff_triplet_records(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_geotiff_triplet()
    result, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)

    assert result.returncode == 0
    assert payload is not None
    observed = payload_dataset(payload)
    expected = canonical_dataset(dataset)
    assert _vlrs_from(observed) == _vlrs_from(expected)


def test_render_geotiff_triplet_records(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_geotiff_triplet()
    result, payload = run_las(submission_command, encode_request_for_render(dataset), tmp_path)

    assert result.returncode == 0
    assert payload is not None
    rendered = payload_las_bytes(payload)
    expected = encode_dataset(dataset)
    assert _vlr_payloads(rendered) == _vlr_payloads(expected)


def test_inspect_wkt_pair_records(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_wkt_pair()
    result, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)

    assert result.returncode == 0
    assert payload is not None
    observed = payload_dataset(payload)
    expected = canonical_dataset(dataset)
    assert _vlrs_from(observed) == _vlrs_from(expected)


def test_inspect_classification_lookup_and_text_area_description(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_classification_lookup()
    result, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)

    assert result.returncode == 0
    assert payload is not None
    observed = payload_dataset(payload)
    expected = canonical_dataset(dataset)
    assert _vlrs_from(observed) == _vlrs_from(expected)


def test_inspect_unknown_vlr_and_evlr_as_opaque(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_unknown_records()
    result, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)

    assert result.returncode == 0
    assert payload is not None
    observed = payload_dataset(payload)
    expected = canonical_dataset(dataset)
    assert _vlrs_from(observed) == _vlrs_from(expected)
    assert _evlrs_from(observed) == _evlrs_from(expected)


def test_inspect_extra_bytes_vlr_and_point_payload(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_extra_bytes(6)
    result, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)

    assert result.returncode == 0
    assert payload is not None
    observed = payload_dataset(payload)
    expected = canonical_dataset(dataset)
    assert _vlrs_from(observed) == _vlrs_from(expected)
    assert (
        _points_from(observed)[0]["extra_bytes_b64"] == _points_from(expected)[0]["extra_bytes_b64"]
    )


def test_inspect_multiple_evlrs_preserves_order_and_offsets(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_multiple_evlrs()
    result, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)

    assert result.returncode == 0
    assert payload is not None
    observed = payload_dataset(payload)
    expected = canonical_dataset(dataset)
    assert _evlrs_from(observed) == _evlrs_from(expected)
    assert (
        observed["header"]["start_of_first_extended_variable_length_record"]
        == expected["header"]["start_of_first_extended_variable_length_record"]
    )
    assert (
        observed["header"]["number_of_extended_variable_length_records"]
        == expected["header"]["number_of_extended_variable_length_records"]
    )


@pytest.mark.parametrize("data_type", [1, 2, 9, 10, 11, 17, 21, 29, 30])
def test_inspect_extra_bytes_storage_types(
    submission_command: Sequence[str],
    tmp_path: Path,
    data_type: int,
) -> None:
    dataset = dataset_with_extra_bytes_type(data_type)
    result, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)

    assert result.returncode == 0
    assert payload is not None
    observed = payload_dataset(payload)
    expected = canonical_dataset(dataset)
    assert _vlrs_from(observed)[-1] == _vlrs_from(expected)[-1]
    assert (
        _points_from(observed)[0]["extra_bytes_b64"] == _points_from(expected)[0]["extra_bytes_b64"]
    )


def test_render_extra_bytes_dataset(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_extra_bytes(6)
    result, payload = run_las(submission_command, encode_request_for_render(dataset), tmp_path)

    assert result.returncode == 0
    assert payload is not None
    rendered = payload_las_bytes(payload)
    expected = encode_dataset(dataset)
    assert _vlr_payloads(rendered) == _vlr_payloads(expected)


def test_inspect_undocumented_extra_bytes_descriptor(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(6)
    dataset["vlrs"].append(undocumented_extra_bytes_vlr(2))
    dataset["points"] = [dataset["points"][0] | {"extra_bytes_b64": "NBI="}]
    result, payload = run_las(submission_command, encode_request_for_inspect(dataset), tmp_path)

    assert result.returncode == 0
    assert payload is not None
    observed = payload_dataset(payload)
    expected = canonical_dataset(dataset)
    assert _vlrs_from(observed)[-1] == _vlrs_from(expected)[-1]
    assert (
        _points_from(observed)[0]["extra_bytes_b64"] == _points_from(expected)[0]["extra_bytes_b64"]
    )


def test_render_empty_point_list_round_trips(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(6)
    dataset["points"] = []
    render_result, render_payload = run_las(
        submission_command,
        encode_request_for_render(dataset),
        tmp_path,
    )

    assert render_result.returncode == 0
    assert render_payload is not None
    assert payload_las_bytes(render_payload) == encode_dataset(dataset)


def test_render_waveform_dataset(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(9)
    result, payload = run_las(submission_command, encode_request_for_render(dataset), tmp_path)

    assert result.returncode == 0
    assert payload is not None
    rendered = payload_las_bytes(payload)
    expected = encode_dataset(dataset)
    assert _vlr_payloads(rendered) == _vlr_payloads(expected)
    assert _evlr_payloads(rendered) == _evlr_payloads(expected)
