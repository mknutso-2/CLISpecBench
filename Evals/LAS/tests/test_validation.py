from __future__ import annotations

import base64
import struct
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import pytest

from .conftest import run_las
from .las_support import (
    clone,
    dataset_for_point_format,
    dataset_with_extra_bytes,
    encode_dataset,
    encode_request_for_render,
    extra_bytes_vlr,
    geo_key_directory_vlr,
)


def _patch_bytes(source: bytes, offset: int, replacement: bytes) -> bytes:
    blob = bytearray(source)
    blob[offset : offset + len(replacement)] = replacement
    return bytes(blob)


def _inspect_error_code(
    submission_command: Sequence[str],
    tmp_path: Path,
    data: bytes,
) -> str:
    result, payload = run_las(
        submission_command,
        {"action": "inspect", "las_b64": base64.b64encode(data).decode("ascii")},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    error = cast(dict[str, Any] | None, payload.get("error"))
    assert isinstance(error, dict)
    code = error.get("code")
    assert isinstance(code, str)
    return code


def _render_error_code(
    submission_command: Sequence[str],
    tmp_path: Path,
    dataset: dict[str, Any],
) -> str:
    result, payload = run_las(submission_command, encode_request_for_render(dataset), tmp_path)
    assert result.returncode == 1
    assert payload is not None
    error = cast(dict[str, Any] | None, payload.get("error"))
    assert isinstance(error, dict)
    code = error.get("code")
    assert isinstance(code, str)
    return code


def test_rejects_invalid_file_signature(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(0))
    broken = _patch_bytes(data, 0, b"BAD!")
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_inspect_rejects_malformed_base64_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    result, payload = run_las(
        submission_command,
        {"action": "inspect", "las_b64": "!!!!"},
        tmp_path,
    )

    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_rejects_invalid_header_size(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(0))
    broken = _patch_bytes(data, 94, (374).to_bytes(2, "little"))
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_reserved_global_encoding_bits(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(0))
    broken = _patch_bytes(data, 6, (1 << 7).to_bytes(2, "little"))
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_mutually_exclusive_waveform_bits(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(4))
    broken = _patch_bytes(data, 6, ((1 << 1) | (1 << 2)).to_bytes(2, "little"))
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_modern_point_format_without_wkt_bit(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(6)
    dataset["header"]["global_encoding"] = 0
    data = encode_dataset(dataset)
    assert _inspect_error_code(submission_command, tmp_path, data) == "invalid_document"


def test_rejects_missing_geokeydirectory_in_geotiff_mode(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["vlrs"] = []
    data = encode_dataset(dataset)
    assert _inspect_error_code(submission_command, tmp_path, data) == "invalid_document"


def test_rejects_missing_coordinate_system_wkt_record(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(6)
    dataset["vlrs"] = []
    data = encode_dataset(dataset)
    assert _inspect_error_code(submission_command, tmp_path, data) == "invalid_document"


def test_rejects_duplicate_geokeydirectory_records(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["vlrs"].append(clone(dataset["vlrs"][0]))
    data = encode_dataset(dataset)
    assert _inspect_error_code(submission_command, tmp_path, data) == "invalid_document"


def test_rejects_duplicate_coordinate_system_wkt_records(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(6)
    dataset["vlrs"].append(clone(dataset["vlrs"][0]))
    data = encode_dataset(dataset)
    assert _inspect_error_code(submission_command, tmp_path, data) == "invalid_document"


def test_rejects_truncated_point_data(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(6))
    broken = data[:-5]
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_vlr_reserved_field_nonzero(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(0))
    broken = _patch_bytes(data, 375, b"\x01\x00")
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_evlr_reserved_field_nonzero(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(9))
    evlr_offset = int.from_bytes(data[235:243], "little")
    broken = _patch_bytes(data, evlr_offset, b"\x01\x00")
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_invalid_classification_lookup_length(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["vlrs"].append(
        {
            "user_id": "LASF_Spec",
            "record_id": 0,
            "description": "BadLookup",
            "kind": "opaque",
            "data_b64": base64.b64encode(b"\x00" * 32).decode("ascii"),
        }
    )
    data = encode_dataset(dataset)
    assert _inspect_error_code(submission_command, tmp_path, data) == "invalid_document"


def test_rejects_text_area_without_null_terminator(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["vlrs"].append(
        {
            "user_id": "LASF_Spec",
            "record_id": 3,
            "description": "BadText",
            "kind": "opaque",
            "data_b64": base64.b64encode(b"not-terminated").decode("ascii"),
        }
    )
    data = encode_dataset(dataset)
    assert _inspect_error_code(submission_command, tmp_path, data) == "invalid_document"


def test_rejects_wkt_without_null_terminator(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(6)
    dataset["vlrs"] = [
        {
            "user_id": "LASF_Projection",
            "record_id": 2112,
            "description": "BadWKT",
            "kind": "opaque",
            "data_b64": base64.b64encode(b"PROJCS[bad]").decode("ascii"),
        }
    ]
    data = encode_dataset(dataset)
    assert _inspect_error_code(submission_command, tmp_path, data) == "invalid_document"


def test_rejects_bad_geokeydirectory_header(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(0))
    broken = _patch_bytes(data, 429, (2).to_bytes(2, "little"))
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_extra_bytes_payload_length_not_multiple_of_192(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_extra_bytes(6)
    dataset["vlrs"][-1] = {
        "user_id": "LASF_Spec",
        "record_id": 4,
        "description": "BadExtra",
        "kind": "opaque",
        "data_b64": base64.b64encode(b"\x00" * 10).decode("ascii"),
    }
    data = encode_dataset(dataset)
    assert _inspect_error_code(submission_command, tmp_path, data) == "invalid_document"


def test_rejects_extra_bytes_mismatch(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_extra_bytes(6)
    descriptor = dataset["vlrs"][-1]["descriptors"][0]
    descriptor["data_type"] = 7
    data = encode_dataset(dataset)
    assert _inspect_error_code(submission_command, tmp_path, data) == "invalid_document"


def test_rejects_extra_bytes_reserved_bytes_nonzero(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_with_extra_bytes(6))
    first_vlr_length = int.from_bytes(data[395:397], "little")
    extra_vlr_header_offset = 375 + 54 + first_vlr_length
    extra_vlr_payload_offset = extra_vlr_header_offset + 54
    broken = _patch_bytes(data, extra_vlr_payload_offset, b"\x01\x00")
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_extra_bytes_unused_field_nonzero(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_with_extra_bytes(6))
    first_vlr_length = int.from_bytes(data[395:397], "little")
    extra_vlr_header_offset = 375 + 54 + first_vlr_length
    extra_vlr_payload_offset = extra_vlr_header_offset + 54
    broken = _patch_bytes(data, extra_vlr_payload_offset + 36, b"\x01\x00\x00\x00")
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_invalid_waveform_descriptor_length(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(9)
    dataset["vlrs"][1] = {
        "user_id": "LASF_Spec",
        "record_id": 100,
        "description": "WaveDesc",
        "kind": "opaque",
        "data_b64": base64.b64encode(b"\x00" * 10).decode("ascii"),
    }
    data = encode_dataset(dataset)
    assert _inspect_error_code(submission_command, tmp_path, data) == "invalid_document"


def test_rejects_waveform_bits_per_sample_out_of_range(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(9))
    first_vlr_length = int.from_bytes(data[395:397], "little")
    waveform_payload_offset = 375 + 54 + first_vlr_length + 54
    broken = _patch_bytes(data, waveform_payload_offset, b"\x01")
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_waveform_bits_per_sample_above_32(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(9))
    first_vlr_length = int.from_bytes(data[395:397], "little")
    waveform_payload_offset = 375 + 54 + first_vlr_length + 54
    broken = _patch_bytes(data, waveform_payload_offset, b"\x21")
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_waveform_compression_type_nonzero(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(9))
    first_vlr_length = int.from_bytes(data[395:397], "little")
    waveform_payload_offset = 375 + 54 + first_vlr_length + 54
    broken = _patch_bytes(data, waveform_payload_offset + 1, b"\x01")
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_missing_waveform_descriptor_reference(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(9)
    dataset["points"][0]["waveform"]["descriptor_index"] = 2
    data = encode_dataset(dataset)
    assert _inspect_error_code(submission_command, tmp_path, data) == "invalid_document"


def test_rejects_internal_waveform_bit_without_waveform_evlr(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(9)
    dataset["evlrs"] = []
    data = encode_dataset(dataset)
    assert _inspect_error_code(submission_command, tmp_path, data) == "invalid_document"


def test_rejects_waveform_evlr_without_internal_bit(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(9)
    dataset["header"]["global_encoding"] = dataset["header"]["global_encoding"] & ~0x02
    data = encode_dataset(dataset)
    assert _inspect_error_code(submission_command, tmp_path, data) == "invalid_document"


def test_rejects_zero_return_number_in_modern_format(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(6))
    point_offset = int.from_bytes(data[96:100], "little")
    broken = _patch_bytes(data, point_offset + 14, b"\x00")
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_scan_angle_rank_out_of_range(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(0))
    point_offset = int.from_bytes(data[96:100], "little")
    broken = _patch_bytes(data, point_offset + 16, (120).to_bytes(1, "little", signed=True))
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_modern_scan_angle_out_of_range(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(6))
    point_offset = int.from_bytes(data[96:100], "little")
    broken = _patch_bytes(data, point_offset + 18, (30001).to_bytes(2, "little", signed=True))
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_offset_to_point_data_smaller_than_header(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(0))
    broken = _patch_bytes(data, 96, (374).to_bytes(4, "little"))
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_number_of_point_records_mismatch(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(6))
    broken = _patch_bytes(data, 247, (2).to_bytes(8, "little"))
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_number_of_points_by_return_mismatch(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(6))
    broken = _patch_bytes(data, 255, (0).to_bytes(8, "little"))
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_nonzero_legacy_counters_for_modern_point_format(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(6))
    broken = _patch_bytes(data, 107, (1).to_bytes(4, "little"))
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_legacy_count_zero_with_populated_return_counters(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(0))
    broken = _patch_bytes(data, 107, (0).to_bytes(4, "little"))
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_legacy_count_populated_with_zero_return_counters(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(0))
    broken = _patch_bytes(data, 111, b"\x00" * 20)
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_rejects_header_extent_mismatch(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    data = encode_dataset(dataset_for_point_format(6))
    broken = _patch_bytes(data, 179, struct.pack("<d", 999.0))
    assert _inspect_error_code(submission_command, tmp_path, broken) == "invalid_document"


def test_render_rejects_color_for_legacy_non_color_format(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["points"][0]["color"] = {"red": 1, "green": 2, "blue": 3}
    result, payload = run_las(submission_command, encode_request_for_render(dataset), tmp_path)

    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_mismatched_extra_bytes_lengths(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_extra_bytes(6)
    second = clone(dataset["points"][0])
    second["extra_bytes_b64"] = base64.b64encode(b"\x00\x01\x02\x03").decode("ascii")
    dataset["points"].append(second)
    result, payload = run_las(submission_command, encode_request_for_render(dataset), tmp_path)

    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_waveform_data_packets_in_vlrs(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(9)
    dataset["vlrs"].append(dataset["evlrs"].pop())
    result, payload = run_las(submission_command, encode_request_for_render(dataset), tmp_path)

    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_reserved_global_encoding_bits_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(6)
    dataset["header"]["global_encoding"] = dataset["header"]["global_encoding"] | (1 << 7)
    result, payload = run_las(submission_command, encode_request_for_render(dataset), tmp_path)

    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_header_uint16_overflow_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["header"]["file_source_id"] = 70000

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_invalid_project_id_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["header"]["project_id"] = "not-a-uuid"

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


@pytest.mark.parametrize("header_field", ["system_identifier", "generating_software"])
def test_render_rejects_non_ascii_header_text_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
    header_field: str,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["header"][header_field] = "Caf\u00e9"

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_embedded_nul_in_fixed_ascii_header_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["header"]["system_identifier"] = "A\x00B"

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


@pytest.mark.parametrize("field", ["user_id", "description"])
def test_render_rejects_non_ascii_record_header_text_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
    field: str,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["vlrs"].append(
        {
            "user_id": "CUSTOM",
            "record_id": 42,
            "description": "Opaque",
            "kind": "opaque",
            "data_b64": "",
        }
    )
    dataset["vlrs"][-1][field] = "Caf\u00e9"

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_embedded_nul_in_record_description_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["vlrs"].append(
        {
            "user_id": "CUSTOM",
            "record_id": 42,
            "description": "A\x00B",
            "kind": "opaque",
            "data_b64": "",
        }
    )

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_non_ascii_text_area_payload_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["vlrs"].append(
        {
            "user_id": "LASF_Spec",
            "record_id": 3,
            "description": "Text",
            "kind": "text_area_description",
            "text": "Caf\u00e9",
        }
    )

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_non_ascii_geo_ascii_payload_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["vlrs"].append(
        {
            "user_id": "LASF_Projection",
            "record_id": 34737,
            "description": "GeoASCII",
            "kind": "geo_ascii_params",
            "text": "Caf\u00e9",
        }
    )

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


@pytest.mark.parametrize(
    ("point_format", "target", "field"),
    [
        (0, "header", "x_scale_factor"),
        (6, "point", "gps_time"),
        (9, "waveform", "xt"),
        (9, "waveform", "return_point_waveform_location"),
    ],
)
def test_render_rejects_numeric_values_that_do_not_fit_target_binary_float(
    submission_command: Sequence[str],
    tmp_path: Path,
    point_format: int,
    target: str,
    field: str,
) -> None:
    dataset = dataset_for_point_format(point_format)
    if target == "header":
        dataset["header"][field] = 10**1000
    elif target == "point":
        dataset["points"][0][field] = 10**1000
    else:
        dataset["points"][0]["waveform"][field] = 1e100

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_modern_geotiff_mode_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(6)
    dataset["header"]["global_encoding"] = 0
    dataset["vlrs"] = [geo_key_directory_vlr()]
    result, payload = run_las(submission_command, encode_request_for_render(dataset), tmp_path)

    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_missing_waveform_descriptor_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(9)
    dataset["vlrs"] = [dataset["vlrs"][0]]
    result, payload = run_las(submission_command, encode_request_for_render(dataset), tmp_path)

    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_extra_bytes_descriptor_longer_than_point_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(6)
    dataset["vlrs"].append(extra_bytes_vlr())
    result, payload = run_las(submission_command, encode_request_for_render(dataset), tmp_path)

    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_invalid_extra_bytes_triplet_shape(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_extra_bytes(6)
    dataset["vlrs"][-1]["descriptors"][0]["scale"] = [1.0, 2.0]
    result, payload = run_las(submission_command, encode_request_for_render(dataset), tmp_path)

    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_wrong_user_id_for_geo_key_directory(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["vlrs"][0]["user_id"] = "BAD_USER"
    result, payload = run_las(submission_command, encode_request_for_render(dataset), tmp_path)

    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_malformed_opaque_base64_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["vlrs"].append(
        {
            "user_id": "CUSTOM",
            "record_id": 42,
            "description": "Opaque",
            "kind": "opaque",
            "data_b64": "!!!!",
        }
    )

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_bad_geokeydirectory_header_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["vlrs"][0]["key_directory_version"] = 2

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_geokeydirectory_uint16_overflow_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(0)
    dataset["vlrs"][0]["keys"][0]["key_id"] = 70000

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_waveform_bits_per_sample_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(9)
    dataset["vlrs"][1]["bits_per_sample"] = 1

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_waveform_descriptor_uint8_overflow_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(9)
    dataset["vlrs"][1]["bits_per_sample"] = 256

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_waveform_compression_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(9)
    dataset["vlrs"][1]["waveform_compression_type"] = 1

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_waveform_descriptor_uint32_overflow_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(9)
    dataset["vlrs"][1]["number_of_samples"] = 0x100000000

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_malformed_waveform_data_base64_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(9)
    dataset["evlrs"][0]["data_b64"] = "!!!!"

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_opaque_extra_bytes_reserved_bytes_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(6)
    invalid_descriptor = b"\x01\x00" + (b"\x00" * 190)
    dataset["vlrs"].append(
        {
            "user_id": "LASF_Spec",
            "record_id": 4,
            "description": "BadExtra",
            "kind": "opaque",
            "data_b64": base64.b64encode(invalid_descriptor).decode("ascii"),
        }
    )

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


@pytest.mark.parametrize("data_type", [31, 256])
def test_render_rejects_extra_bytes_descriptor_data_type_outside_supported_range(
    submission_command: Sequence[str],
    tmp_path: Path,
    data_type: int,
) -> None:
    dataset = dataset_with_extra_bytes(6)
    dataset["vlrs"][-1]["descriptors"][0]["data_type"] = data_type

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_extra_bytes_descriptor_options_uint8_overflow(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_extra_bytes(6)
    dataset["vlrs"][-1]["descriptors"][0]["options"] = 256

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_extra_bytes_float_triplet_overflow(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_extra_bytes(6)
    descriptor = dataset["vlrs"][-1]["descriptors"][0]
    descriptor["data_type"] = 9
    descriptor["no_data"][0] = 10**1000

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_malformed_point_extra_bytes_base64_as_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_with_extra_bytes(6)
    dataset["points"][0]["extra_bytes_b64"] = "NBI=!!!!"

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


@pytest.mark.parametrize(
    ("point_format", "field", "value"),
    [
        (0, "intensity", 70000),
        (0, "user_data", 256),
        (0, "point_source_id", 70000),
        (6, "x", 0x80000000),
        (6, "intensity", 70000),
        (6, "classification", 256),
        (6, "user_data", 256),
        (6, "point_source_id", 70000),
        (6, "scanner_channel", 4),
    ],
)
def test_render_rejects_point_scalar_values_outside_las_ranges(
    submission_command: Sequence[str],
    tmp_path: Path,
    point_format: int,
    field: str,
    value: int,
) -> None:
    dataset = dataset_for_point_format(point_format)
    dataset["points"][0][field] = value

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_color_component_outside_uint16(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(7)
    dataset["points"][0]["color"]["red"] = 70000

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


def test_render_rejects_nir_component_outside_uint16(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    dataset = dataset_for_point_format(8)
    dataset["points"][0]["nir"] = 70000

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("descriptor_index", 256),
        ("byte_offset_to_waveform_data", 0x10000000000000000),
        ("waveform_packet_size_in_bytes", 0x100000000),
    ],
)
def test_render_rejects_waveform_integer_values_outside_las_ranges(
    submission_command: Sequence[str],
    tmp_path: Path,
    field: str,
    value: int,
) -> None:
    dataset = dataset_for_point_format(9)
    dataset["points"][0]["waveform"][field] = value

    assert _render_error_code(submission_command, tmp_path, dataset) == "invalid_request"
