from __future__ import annotations

import base64
import copy
import math
import struct
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final, cast

FORMAT_MIN_POINT_LENGTH: Final[dict[int, int]] = {
    0: 20,
    1: 28,
    2: 26,
    3: 34,
    4: 57,
    5: 63,
    6: 30,
    7: 36,
    8: 38,
    9: 59,
    10: 67,
}

LEGACY_FORMATS: Final[set[int]] = {0, 1, 2, 3, 4, 5}
MODERN_FORMATS: Final[set[int]] = {6, 7, 8, 9, 10}
GPS_TIME_FORMATS: Final[set[int]] = {1, 3, 4, 5, 6, 7, 8, 9, 10}
COLOR_FORMATS: Final[set[int]] = {2, 3, 5, 7, 8, 10}
NIR_FORMATS: Final[set[int]] = {8, 10}
WAVEFORM_FORMATS: Final[set[int]] = {4, 5, 9, 10}

LASF_PROJECTION: Final[str] = "LASF_Projection"
LASF_SPEC: Final[str] = "LASF_Spec"

WKT_BIT: Final[int] = 1 << 4
WAVEFORM_INTERNAL_BIT: Final[int] = 1 << 1
WAVEFORM_EXTERNAL_BIT: Final[int] = 1 << 2
FLOAT32_MAX: Final[float] = 3.4028234663852886e38


@dataclass(slots=True)
class LasError(Exception):
    code: str
    message: str
    offset: int | None = None


def inspect_las(request: dict[str, Any]) -> dict[str, Any]:
    las_b64 = request.get("las_b64")
    if not isinstance(las_b64, str):
        raise LasError("invalid_request", "inspect requests must include a las_b64 string")
    data = _decode_base64_text(las_b64, "las_b64")
    return _inspect_bytes(data)


def render_las(dataset: dict[str, Any]) -> str:
    data = _render_bytes(dataset)
    return base64.b64encode(data).decode("ascii")


def _decode_base64_text(
    text: str,
    field_name: str,
    *,
    error_code: str = "invalid_request",
) -> bytes:
    try:
        return base64.b64decode(text.encode("ascii"), validate=True)
    except Exception as exc:
        raise LasError(error_code, f"{field_name} is not valid base64: {exc}") from exc


def _inspect_bytes(data: bytes) -> dict[str, Any]:
    if len(data) < 375:
        raise LasError("invalid_document", "LAS file is shorter than the LAS 1.4 public header")
    if data[:4] != b"LASF":
        raise LasError("invalid_document", 'File signature must be "LASF"', offset=0)

    header = _parse_header(data)
    offset_to_point_data = _get_int(header, "offset_to_point_data")
    number_of_vlrs = _get_int(header, "number_of_variable_length_records")
    point_format = _get_int(header, "point_data_record_format")
    point_record_length = _get_int(header, "point_data_record_length")
    number_of_evlrs = _get_int(header, "number_of_extended_variable_length_records")
    first_evlr_offset = _get_int(header, "start_of_first_extended_variable_length_record")

    if offset_to_point_data < 375:
        raise LasError("invalid_document", "offset_to_point_data must be at least 375", offset=96)
    if point_format not in FORMAT_MIN_POINT_LENGTH:
        raise LasError("invalid_document", "Unsupported LAS point format", offset=104)
    if point_record_length < FORMAT_MIN_POINT_LENGTH[point_format]:
        raise LasError(
            "invalid_document", "Point record length is smaller than the format minimum", offset=105
        )

    cursor = 375
    vlrs: list[dict[str, Any]] = []
    standard_records: list[_DecodedRecord] = []
    for _ in range(number_of_vlrs):
        record, cursor = _parse_variable_record(
            data,
            cursor,
            limit=offset_to_point_data,
            is_evlr=False,
        )
        vlrs.append(record.record)
        standard_records.append(record)
    if cursor > offset_to_point_data:
        raise LasError("invalid_document", "VLRs run past offset_to_point_data", offset=cursor)

    point_count = _point_count_for_reading(header)
    points_start = offset_to_point_data
    points_end = points_start + (point_count * point_record_length)
    if first_evlr_offset:
        if number_of_evlrs == 0:
            raise LasError(
                "invalid_document",
                "start_of_first_extended_variable_length_record is non-zero but EVLR count is zero",
                offset=235,
            )
        if points_end > first_evlr_offset:
            raise LasError(
                "invalid_document",
                "Point data runs past the first EVLR offset",
                offset=first_evlr_offset,
            )
        points_limit = first_evlr_offset
    else:
        if number_of_evlrs != 0:
            raise LasError(
                "invalid_document",
                "EVLR count is non-zero but start_of_first_extended_variable_length_record is zero",
                offset=243,
            )
        points_limit = len(data)
    if points_end > points_limit:
        raise LasError("invalid_document", "Point data is truncated", offset=points_start)

    points: list[dict[str, Any]] = []
    point_cursor = points_start
    for index in range(point_count):
        point = _parse_point(
            data[point_cursor : point_cursor + point_record_length],
            point_format=point_format,
            point_record_length=point_record_length,
            offset=point_cursor,
        )
        points.append(point)
        point_cursor += point_record_length
        _ = index

    evlrs: list[dict[str, Any]] = []
    decoded_evlrs: list[_DecodedRecord] = []
    evlr_cursor = first_evlr_offset
    for _ in range(number_of_evlrs):
        record, evlr_cursor = _parse_variable_record(
            data,
            evlr_cursor,
            limit=len(data),
            is_evlr=True,
        )
        evlrs.append(record.record)
        decoded_evlrs.append(record)

    _validate_global_encoding(_get_int(header, "global_encoding"), header_offset=6)
    _validate_public_header_counters(header, points)
    _validate_crs(header, standard_records, decoded_evlrs)
    _validate_waveform_semantics(header, points, standard_records, decoded_evlrs)
    _validate_extra_bytes_semantics(header, points, standard_records)

    return {
        "header": header,
        "vlrs": vlrs,
        "points": points,
        "evlrs": evlrs,
    }


def _render_bytes(dataset: dict[str, Any]) -> bytes:
    canonical = _canonicalize_render_dataset(dataset)
    header = cast(dict[str, Any], canonical["header"])
    vlrs = cast(list[_RenderedRecord], canonical["_vlrs"])
    points = cast(list[bytes], canonical["_point_bytes"])
    evlrs = cast(list[_RenderedRecord], canonical["_evlrs"])

    blob = bytearray()
    blob.extend(b"LASF")
    blob.extend(
        struct.pack(
            "<HH",
            _get_uint16(header, "file_source_id"),
            _get_uint16(header, "global_encoding"),
        )
    )
    blob.extend(_uuid_bytes_le(_get_str(header, "project_id"), "header.project_id"))
    blob.extend(
        struct.pack(
            "<BB",
            _get_uint8(header, "version_major"),
            _get_uint8(header, "version_minor"),
        )
    )
    blob.extend(
        _encode_fixed_ascii(_get_str(header, "system_identifier"), 32, "header.system_identifier")
    )
    blob.extend(
        _encode_fixed_ascii(
            _get_str(header, "generating_software"),
            32,
            "header.generating_software",
        )
    )
    blob.extend(
        struct.pack(
            "<HHHLLBH",
            _get_uint16(header, "file_creation_day_of_year"),
            _get_uint16(header, "file_creation_year"),
            _get_uint16(header, "header_size"),
            _get_uint32(header, "offset_to_point_data"),
            _get_uint32(header, "number_of_variable_length_records"),
            _get_uint8(header, "point_data_record_format"),
            _get_uint16(header, "point_data_record_length"),
        )
    )
    blob.extend(
        struct.pack(
            "<L5L",
            _get_uint32(header, "legacy_number_of_point_records"),
            *[
                _ensure_uint32(value, "legacy_number_of_points_by_return")
                for value in cast(list[Any], header["legacy_number_of_points_by_return"])
            ],
        )
    )
    blob.extend(
        struct.pack(
            "<12d",
            _get_number(header, "x_scale_factor"),
            _get_number(header, "y_scale_factor"),
            _get_number(header, "z_scale_factor"),
            _get_number(header, "x_offset"),
            _get_number(header, "y_offset"),
            _get_number(header, "z_offset"),
            _get_number(header, "max_x"),
            _get_number(header, "min_x"),
            _get_number(header, "max_y"),
            _get_number(header, "min_y"),
            _get_number(header, "max_z"),
            _get_number(header, "min_z"),
        )
    )
    blob.extend(
        struct.pack(
            "<QQLQ15Q",
            _get_uint64(header, "start_of_waveform_data_packet_record"),
            _get_uint64(header, "start_of_first_extended_variable_length_record"),
            _get_uint32(header, "number_of_extended_variable_length_records"),
            _get_uint64(header, "number_of_point_records"),
            *[
                _ensure_uint64(value, "number_of_points_by_return")
                for value in cast(list[Any], header["number_of_points_by_return"])
            ],
        )
    )
    if len(blob) != 375:
        raise LasError("internal_error", "Internal LAS header packing bug")

    for record in vlrs:
        blob.extend(struct.pack("<H", 0))
        blob.extend(_encode_fixed_ascii(record.user_id, 16, "record.user_id"))
        blob.extend(struct.pack("<H", record.record_id))
        blob.extend(struct.pack("<H", len(record.payload)))
        blob.extend(_encode_fixed_ascii(record.description, 32, "record.description"))
        blob.extend(record.payload)
    for point in points:
        blob.extend(point)
    for record in evlrs:
        blob.extend(struct.pack("<H", 0))
        blob.extend(_encode_fixed_ascii(record.user_id, 16, "record.user_id"))
        blob.extend(struct.pack("<H", record.record_id))
        blob.extend(struct.pack("<Q", len(record.payload)))
        blob.extend(_encode_fixed_ascii(record.description, 32, "record.description"))
        blob.extend(record.payload)
    return bytes(blob)


def _parse_header(data: bytes) -> dict[str, Any]:
    project_id = str(uuid.UUID(bytes_le=data[8:24]))
    system_identifier = _decode_padded_ascii(data[26:58], "system_identifier", 26)
    generating_software = _decode_padded_ascii(data[58:90], "generating_software", 58)
    (
        file_source_id,
        global_encoding,
    ) = struct.unpack_from("<HH", data, 4)
    (
        version_major,
        version_minor,
    ) = struct.unpack_from("<BB", data, 24)
    (
        file_creation_day_of_year,
        file_creation_year,
        header_size,
        offset_to_point_data,
        number_of_variable_length_records,
        point_data_record_format,
        point_data_record_length,
        legacy_number_of_point_records,
    ) = struct.unpack_from("<HHHLLBHL", data, 90)
    legacy_number_of_points_by_return = list(struct.unpack_from("<5L", data, 111))
    (
        x_scale_factor,
        y_scale_factor,
        z_scale_factor,
        x_offset,
        y_offset,
        z_offset,
        max_x,
        min_x,
        max_y,
        min_y,
        max_z,
        min_z,
    ) = struct.unpack_from("<12d", data, 131)
    (
        start_of_waveform_data_packet_record,
        start_of_first_extended_variable_length_record,
        number_of_extended_variable_length_records,
        number_of_point_records,
    ) = struct.unpack_from("<QQLQ", data, 227)
    number_of_points_by_return = list(struct.unpack_from("<15Q", data, 255))

    if version_major != 1 or version_minor != 4:
        raise LasError("invalid_document", "Only LAS 1.4 files are supported", offset=24)
    if header_size != 375:
        raise LasError("invalid_document", "LAS 1.4 header_size must be 375", offset=94)

    return {
        "file_source_id": file_source_id,
        "global_encoding": global_encoding,
        "project_id": project_id,
        "version_major": version_major,
        "version_minor": version_minor,
        "system_identifier": system_identifier,
        "generating_software": generating_software,
        "file_creation_day_of_year": file_creation_day_of_year,
        "file_creation_year": file_creation_year,
        "header_size": header_size,
        "offset_to_point_data": offset_to_point_data,
        "number_of_variable_length_records": number_of_variable_length_records,
        "point_data_record_format": point_data_record_format,
        "point_data_record_length": point_data_record_length,
        "legacy_number_of_point_records": legacy_number_of_point_records,
        "legacy_number_of_points_by_return": legacy_number_of_points_by_return,
        "x_scale_factor": x_scale_factor,
        "y_scale_factor": y_scale_factor,
        "z_scale_factor": z_scale_factor,
        "x_offset": x_offset,
        "y_offset": y_offset,
        "z_offset": z_offset,
        "max_x": max_x,
        "min_x": min_x,
        "max_y": max_y,
        "min_y": min_y,
        "max_z": max_z,
        "min_z": min_z,
        "start_of_waveform_data_packet_record": start_of_waveform_data_packet_record,
        "start_of_first_extended_variable_length_record": (
            start_of_first_extended_variable_length_record
        ),
        "number_of_extended_variable_length_records": number_of_extended_variable_length_records,
        "number_of_point_records": number_of_point_records,
        "number_of_points_by_return": number_of_points_by_return,
    }


def _parse_variable_record(
    data: bytes,
    cursor: int,
    *,
    limit: int,
    is_evlr: bool,
) -> tuple[_DecodedRecord, int]:
    header_size = 60 if is_evlr else 54
    if cursor < 0 or cursor + header_size > limit or cursor + header_size > len(data):
        raise LasError("invalid_document", "Truncated VLR/EVLR header", offset=cursor)
    reserved = struct.unpack_from("<H", data, cursor)[0]
    if reserved != 0:
        raise LasError("invalid_document", "VLR/EVLR reserved field must be zero", offset=cursor)
    user_id = _decode_padded_ascii(data[cursor + 2 : cursor + 18], "record.user_id", cursor + 2)
    record_id = struct.unpack_from("<H", data, cursor + 18)[0]
    if is_evlr:
        record_length = struct.unpack_from("<Q", data, cursor + 20)[0]
        description = _decode_padded_ascii(
            data[cursor + 28 : cursor + 60],
            "record.description",
            cursor + 28,
        )
        payload_offset = cursor + 60
    else:
        record_length = struct.unpack_from("<H", data, cursor + 20)[0]
        description = _decode_padded_ascii(
            data[cursor + 22 : cursor + 54],
            "record.description",
            cursor + 22,
        )
        payload_offset = cursor + 54
    payload_end = payload_offset + record_length
    if payload_end > limit or payload_end > len(data):
        raise LasError("invalid_document", "VLR/EVLR payload is truncated", offset=payload_offset)
    payload = data[payload_offset:payload_end]
    record = _decode_record(
        user_id=user_id,
        record_id=record_id,
        description=description,
        payload=payload,
        payload_offset=payload_offset,
        is_evlr=is_evlr,
    )
    record.header_offset = cursor
    return record, payload_end


def _decode_record(
    *,
    user_id: str,
    record_id: int,
    description: str,
    payload: bytes,
    payload_offset: int,
    is_evlr: bool,
) -> _DecodedRecord:
    record: dict[str, Any] = {
        "user_id": user_id,
        "record_id": record_id,
        "description": description,
    }
    if (user_id, record_id) == (LASF_SPEC, 0):
        if len(payload) != 256 * 16:
            raise LasError(
                "invalid_document",
                "Classification lookup payload must be 4096 bytes",
                offset=payload_offset,
            )
        entries: list[dict[str, Any]] = []
        for index in range(256):
            base = index * 16
            class_number = payload[base]
            text = _decode_padded_ascii(
                payload[base + 1 : base + 16], "classification_lookup", payload_offset + base + 1
            )
            if text:
                entries.append({"class_number": class_number, "description": text})
        record["kind"] = "classification_lookup"
        record["entries"] = entries
        return _DecodedRecord(record=record, kind="classification_lookup", payload=payload)
    if (user_id, record_id) == (LASF_SPEC, 3):
        record["kind"] = "text_area_description"
        record["text"] = _decode_null_terminated_ascii(
            payload, "text_area_description", payload_offset
        )
        return _DecodedRecord(record=record, kind="text_area_description", payload=payload)
    if (user_id, record_id) == (LASF_SPEC, 4):
        if len(payload) % 192 != 0:
            raise LasError(
                "invalid_document",
                "Extra Bytes payload length must be a multiple of 192",
                offset=payload_offset,
            )
        descriptors: list[dict[str, Any]] = []
        total_described_bytes = 0
        for index in range(len(payload) // 192):
            descriptor_offset = payload_offset + (index * 192)
            descriptor, described_bytes = _decode_extra_bytes_descriptor(
                payload[index * 192 : (index + 1) * 192],
                offset=descriptor_offset,
            )
            descriptors.append(descriptor)
            total_described_bytes += described_bytes
        record["kind"] = "extra_bytes"
        record["descriptors"] = descriptors
        return _DecodedRecord(
            record=record,
            kind="extra_bytes",
            payload=payload,
            described_extra_bytes=total_described_bytes,
        )
    if user_id == LASF_SPEC and 100 <= record_id <= 354:
        if len(payload) != 26:
            raise LasError(
                "invalid_document",
                "Waveform Packet Descriptor payload must be 26 bytes",
                offset=payload_offset,
            )
        (
            bits_per_sample,
            compression_type,
            number_of_samples,
            temporal_sample_spacing,
            digitizer_gain,
            digitizer_offset,
        ) = struct.unpack(
            "<BBLLdd",
            payload,
        )
        if not 2 <= bits_per_sample <= 32:
            raise LasError(
                "invalid_document",
                "Waveform bits_per_sample must be between 2 and 32",
                offset=payload_offset,
            )
        if compression_type != 0:
            raise LasError(
                "invalid_document",
                "Only waveform compression type 0 is supported",
                offset=payload_offset + 1,
            )
        record["kind"] = "waveform_packet_descriptor"
        record["bits_per_sample"] = bits_per_sample
        record["waveform_compression_type"] = compression_type
        record["number_of_samples"] = number_of_samples
        record["temporal_sample_spacing"] = temporal_sample_spacing
        record["digitizer_gain"] = digitizer_gain
        record["digitizer_offset"] = digitizer_offset
        return _DecodedRecord(record=record, kind="waveform_packet_descriptor", payload=payload)
    if (user_id, record_id) == (LASF_SPEC, 65535):
        if not is_evlr:
            raise LasError(
                "invalid_document",
                "Waveform data packets must be stored in EVLRs",
                offset=payload_offset,
            )
        record["kind"] = "waveform_data_packets"
        record["data_b64"] = base64.b64encode(payload).decode("ascii")
        return _DecodedRecord(record=record, kind="waveform_data_packets", payload=payload)
    if (user_id, record_id) == (LASF_SPEC, 7):
        record["kind"] = "superseded"
        record["data_b64"] = base64.b64encode(payload).decode("ascii")
        return _DecodedRecord(record=record, kind="superseded", payload=payload)
    if (user_id, record_id) == (LASF_PROJECTION, 2111):
        record["kind"] = "wkt_math_transform"
        record["text"] = _decode_null_terminated_utf8(payload, "wkt_math_transform", payload_offset)
        return _DecodedRecord(record=record, kind="wkt_math_transform", payload=payload)
    if (user_id, record_id) == (LASF_PROJECTION, 2112):
        record["kind"] = "wkt_coordinate_system"
        record["text"] = _decode_null_terminated_utf8(
            payload, "wkt_coordinate_system", payload_offset
        )
        return _DecodedRecord(record=record, kind="wkt_coordinate_system", payload=payload)
    if (user_id, record_id) == (LASF_PROJECTION, 34735):
        if len(payload) < 8 or len(payload) % 2 != 0:
            raise LasError(
                "invalid_document",
                "GeoKeyDirectory payload must contain unsigned shorts",
                offset=payload_offset,
            )
        values = list(struct.unpack(f"<{len(payload) // 2}H", payload))
        key_directory_version, key_revision, minor_revision, number_of_keys = values[:4]
        if (key_directory_version, key_revision, minor_revision) != (1, 1, 0):
            raise LasError(
                "invalid_document", "GeoKeyDirectory header must be 1,1,0", offset=payload_offset
            )
        expected_length = 4 + (number_of_keys * 4)
        if len(values) != expected_length:
            raise LasError(
                "invalid_document",
                "GeoKeyDirectory key count does not match payload length",
                offset=payload_offset,
            )
        keys: list[dict[str, Any]] = []
        for index in range(number_of_keys):
            base = 4 + (index * 4)
            key_id, tiff_tag_location, count, value_offset = values[base : base + 4]
            keys.append(
                {
                    "key_id": key_id,
                    "tiff_tag_location": tiff_tag_location,
                    "count": count,
                    "value_offset": value_offset,
                }
            )
        record["kind"] = "geo_key_directory"
        record["key_directory_version"] = key_directory_version
        record["key_revision"] = key_revision
        record["minor_revision"] = minor_revision
        record["keys"] = keys
        return _DecodedRecord(record=record, kind="geo_key_directory", payload=payload)
    if (user_id, record_id) == (LASF_PROJECTION, 34736):
        if len(payload) % 8 != 0:
            raise LasError(
                "invalid_document",
                "GeoDoubleParams payload must be a multiple of 8 bytes",
                offset=payload_offset,
            )
        values = list(struct.unpack(f"<{len(payload) // 8}d", payload))
        record["kind"] = "geo_double_params"
        record["values"] = values
        return _DecodedRecord(record=record, kind="geo_double_params", payload=payload)
    if (user_id, record_id) == (LASF_PROJECTION, 34737):
        record["kind"] = "geo_ascii_params"
        record["text"] = _decode_ascii_blob(payload, "geo_ascii_params", payload_offset)
        return _DecodedRecord(record=record, kind="geo_ascii_params", payload=payload)

    record["kind"] = "opaque"
    record["data_b64"] = base64.b64encode(payload).decode("ascii")
    return _DecodedRecord(record=record, kind="opaque", payload=payload)


def _parse_point(
    raw: bytes,
    *,
    point_format: int,
    point_record_length: int,
    offset: int,
) -> dict[str, Any]:
    if len(raw) != point_record_length:
        raise LasError("invalid_document", "Point record is truncated", offset=offset)

    x, y, z, intensity = struct.unpack_from("<iiiH", raw, 0)
    point: dict[str, Any] = {
        "x": x,
        "y": y,
        "z": z,
        "intensity": intensity,
    }

    if point_format in LEGACY_FORMATS:
        flags, classification_byte, scan_angle_rank, user_data, point_source_id = (
            struct.unpack_from(
                "<BBbBH",
                raw,
                14,
            )
        )
        return_number = flags & 0x07
        number_of_returns = (flags >> 3) & 0x07
        if not 1 <= return_number <= number_of_returns <= 5:
            raise LasError(
                "invalid_document",
                "Legacy return numbers must be in the range 1..5 and ordered",
                offset=offset + 14,
            )
        if not -90 <= scan_angle_rank <= 90:
            raise LasError(
                "invalid_document", "Scan Angle Rank must be between -90 and 90", offset=offset + 16
            )
        point.update(
            {
                "return_number": return_number,
                "number_of_returns": number_of_returns,
                "scan_direction_flag": bool(flags & 0x40),
                "edge_of_flight_line": bool(flags & 0x80),
                "classification": classification_byte & 0x1F,
                "synthetic": bool(classification_byte & 0x20),
                "key_point": bool(classification_byte & 0x40),
                "withheld": bool(classification_byte & 0x80),
                "scan_angle_rank": scan_angle_rank,
                "user_data": user_data,
                "point_source_id": point_source_id,
            }
        )
        cursor = 20
    else:
        (
            returns_byte,
            flags_byte,
            classification,
            user_data,
            scan_angle,
            point_source_id,
            gps_time,
        ) = struct.unpack_from("<BBBBhHd", raw, 14)
        return_number = returns_byte & 0x0F
        number_of_returns = (returns_byte >> 4) & 0x0F
        if not 1 <= return_number <= number_of_returns <= 15:
            raise LasError(
                "invalid_document",
                "Modern return numbers must be between 1 and Number of Returns",
                offset=offset + 14,
            )
        if not -30000 <= scan_angle <= 30000:
            raise LasError(
                "invalid_document",
                "Scan Angle must be between -30000 and 30000",
                offset=offset + 18,
            )
        point.update(
            {
                "return_number": return_number,
                "number_of_returns": number_of_returns,
                "scan_direction_flag": bool(flags_byte & 0x40),
                "edge_of_flight_line": bool(flags_byte & 0x80),
                "classification": classification,
                "synthetic": bool(flags_byte & 0x01),
                "key_point": bool(flags_byte & 0x02),
                "withheld": bool(flags_byte & 0x04),
                "overlap": bool(flags_byte & 0x08),
                "scanner_channel": (flags_byte >> 4) & 0x03,
                "user_data": user_data,
                "scan_angle": scan_angle,
                "point_source_id": point_source_id,
                "gps_time": gps_time,
            }
        )
        cursor = 30

    if point_format in {1, 3, 4, 5}:
        point["gps_time"] = struct.unpack_from("<d", raw, cursor)[0]
        cursor += 8
    if point_format in COLOR_FORMATS:
        red, green, blue = struct.unpack_from("<HHH", raw, cursor)
        point["color"] = {"red": red, "green": green, "blue": blue}
        cursor += 6
    if point_format in NIR_FORMATS:
        point["nir"] = struct.unpack_from("<H", raw, cursor)[0]
        cursor += 2
    if point_format in WAVEFORM_FORMATS:
        descriptor_index, byte_offset, packet_size, location, xt, yt, zt = struct.unpack_from(
            "<BQLffff",
            raw,
            cursor,
        )
        if descriptor_index == 0:
            if any(value != 0 for value in (byte_offset, packet_size, location, xt, yt, zt)):
                raise LasError(
                    "invalid_document",
                    "Waveform descriptor index 0 requires an all-zero waveform block",
                    offset=offset + cursor,
                )
        else:
            point["waveform"] = {
                "descriptor_index": descriptor_index,
                "byte_offset_to_waveform_data": byte_offset,
                "waveform_packet_size_in_bytes": packet_size,
                "return_point_waveform_location": location,
                "xt": xt,
                "yt": yt,
                "zt": zt,
            }
        cursor += 29
    if cursor < point_record_length:
        point["extra_bytes_b64"] = base64.b64encode(raw[cursor:]).decode("ascii")
    return point


def _validate_global_encoding(value: int, *, header_offset: int) -> None:
    if value & 0xFFE0:
        raise LasError(
            "invalid_document", "Global Encoding reserved bits must be zero", offset=header_offset
        )
    if value & WAVEFORM_INTERNAL_BIT and value & WAVEFORM_EXTERNAL_BIT:
        raise LasError(
            "invalid_document",
            "Waveform Data Packets Internal and External bits are mutually exclusive",
            offset=header_offset,
        )


def _validate_public_header_counters(
    header: dict[str, Any],
    points: list[dict[str, Any]],
) -> None:
    point_format = _get_int(header, "point_data_record_format")
    point_count = len(points)
    legacy_count = _get_int(header, "legacy_number_of_point_records")
    legacy_returns = cast(list[int], header["legacy_number_of_points_by_return"])
    if point_format in MODERN_FORMATS:
        if _get_int(header, "number_of_point_records") != point_count:
            raise LasError(
                "invalid_document",
                "number_of_point_records does not match parsed point data",
                offset=247,
            )

        expected_modern_returns = _counts_by_return(points, 15)
        if cast(list[int], header["number_of_points_by_return"]) != expected_modern_returns:
            raise LasError(
                "invalid_document",
                "number_of_points_by_return does not match parsed point data",
                offset=255,
            )

        if legacy_count != 0 or any(value != 0 for value in legacy_returns):
            raise LasError(
                "invalid_document",
                "Legacy point counters must be zero for point formats 6-10",
                offset=107,
            )

    elif point_format in LEGACY_FORMATS:
        expected_legacy_returns = _counts_by_return(points, 5)
        if legacy_count == 0:
            if any(value != 0 for value in legacy_returns):
                raise LasError(
                    "invalid_document",
                    "Legacy by-return counters must be zero when the legacy point count is zero",
                    offset=111,
                )
        else:
            if legacy_count != point_count:
                raise LasError(
                    "invalid_document",
                    "legacy_number_of_point_records does not match parsed point data",
                    offset=107,
                )
            if legacy_returns != expected_legacy_returns:
                raise LasError(
                    "invalid_document",
                    "legacy_number_of_points_by_return does not match parsed point data",
                    offset=111,
                )

    if points:
        xs, ys, zs = zip(
            *[_point_actual_coordinates(point, header) for point in points], strict=True
        )
        expected_extents = {
            "max_x": max(xs),
            "min_x": min(xs),
            "max_y": max(ys),
            "min_y": min(ys),
            "max_z": max(zs),
            "min_z": min(zs),
        }
    else:
        expected_extents = {
            "max_x": 0.0,
            "min_x": 0.0,
            "max_y": 0.0,
            "min_y": 0.0,
            "max_z": 0.0,
            "min_z": 0.0,
        }
    for key, expected in expected_extents.items():
        if not math.isclose(_get_number(header, key), expected, rel_tol=0.0, abs_tol=1e-9):
            raise LasError("invalid_document", f"{key} does not match parsed point data")


def _point_count_for_reading(header: dict[str, Any]) -> int:
    point_format = _get_int(header, "point_data_record_format")
    legacy_count = _get_int(header, "legacy_number_of_point_records")
    if point_format in LEGACY_FORMATS and legacy_count != 0:
        return legacy_count
    return _get_int(header, "number_of_point_records")


def _validate_crs(
    header: dict[str, Any],
    vlrs: list[_DecodedRecord],
    evlrs: list[_DecodedRecord],
) -> None:
    point_format = _get_int(header, "point_data_record_format")
    global_encoding = _get_int(header, "global_encoding")
    wkt_mode = bool(global_encoding & WKT_BIT)

    records = [*vlrs, *evlrs]
    geo_keys = [record for record in records if record.kind == "geo_key_directory"]
    geo_doubles = [record for record in records if record.kind == "geo_double_params"]
    geo_ascii = [record for record in records if record.kind == "geo_ascii_params"]
    wkt_coordinate = [record for record in records if record.kind == "wkt_coordinate_system"]
    wkt_math = [record for record in records if record.kind == "wkt_math_transform"]

    if len(geo_keys) > 1 or len(geo_doubles) > 1 or len(geo_ascii) > 1:
        raise LasError("invalid_document", "GeoTIFF CRS records must not appear more than once")
    if len(wkt_coordinate) > 1 or len(wkt_math) > 1:
        raise LasError("invalid_document", "WKT CRS records must not appear more than once")

    if wkt_mode:
        if len(wkt_coordinate) != 1:
            raise LasError(
                "invalid_document",
                "WKT mode requires exactly one OGC coordinate system WKT record",
            )
        if point_format in LEGACY_FORMATS and (geo_keys or geo_doubles or geo_ascii):
            raise LasError(
                "invalid_document",
                "Legacy point formats must not mix WKT and GeoTIFF CRS records",
            )
    else:
        if point_format in MODERN_FORMATS:
            raise LasError(
                "invalid_document",
                "Point formats 6-10 must use WKT CRS representation",
                offset=104,
            )
        if len(geo_keys) != 1:
            raise LasError(
                "invalid_document",
                "GeoTIFF mode requires exactly one GeoKeyDirectory record",
            )
        if wkt_coordinate or wkt_math:
            raise LasError(
                "invalid_document",
                "GeoTIFF mode must not include WKT CRS records",
            )


def _validate_waveform_semantics(
    header: dict[str, Any],
    points: list[dict[str, Any]],
    vlrs: list[_DecodedRecord],
    evlrs: list[_DecodedRecord],
) -> None:
    point_format = _get_int(header, "point_data_record_format")
    global_encoding = _get_int(header, "global_encoding")
    internal_waveforms = bool(global_encoding & WAVEFORM_INTERNAL_BIT)
    external_waveforms = bool(global_encoding & WAVEFORM_EXTERNAL_BIT)

    waveform_descriptors = {
        record.record_id - 99 for record in vlrs if record.kind == "waveform_packet_descriptor"
    }
    waveform_data_records = [record for record in evlrs if record.kind == "waveform_data_packets"]

    if point_format not in WAVEFORM_FORMATS:
        if (
            waveform_descriptors
            or waveform_data_records
            or internal_waveforms
            or external_waveforms
        ):
            raise LasError(
                "invalid_document",
                "Non-waveform point formats must not use waveform-specific records or bits",
            )
        return

    nonzero_waveforms = 0
    for point in points:
        waveform = cast(dict[str, Any] | None, point.get("waveform"))
        if waveform is None:
            continue
        nonzero_waveforms += 1
        descriptor_index = _get_int(waveform, "descriptor_index")
        if not waveform_descriptors:
            raise LasError(
                "invalid_document",
                "Waveform points require at least one Waveform Packet Descriptor record",
            )
        if descriptor_index not in waveform_descriptors:
            raise LasError(
                "invalid_document",
                "Waveform descriptor index does not reference an existing "
                "Waveform Packet Descriptor record",
            )

    if waveform_data_records:
        if len(waveform_data_records) > 1:
            raise LasError(
                "invalid_document", "Waveform data packets must not appear more than once"
            )
        if not internal_waveforms:
            raise LasError(
                "invalid_document",
                "Waveform Data Packets EVLR requires the internal waveform global-encoding bit",
            )
        actual_offset = waveform_data_records[0].header_offset
        if _get_int(header, "start_of_waveform_data_packet_record") != actual_offset:
            raise LasError(
                "invalid_document",
                "start_of_waveform_data_packet_record must match the waveform EVLR header offset",
            )
    else:
        if internal_waveforms and nonzero_waveforms:
            raise LasError(
                "invalid_document",
                "Internal waveform bit is set but no waveform data packets EVLR is present",
            )
        if _get_int(header, "start_of_waveform_data_packet_record") != 0:
            raise LasError(
                "invalid_document",
                "start_of_waveform_data_packet_record must be zero when no "
                "waveform data packets EVLR is present",
            )
    if nonzero_waveforms and not (internal_waveforms or external_waveforms):
        raise LasError(
            "invalid_document",
            "Waveform points require either the internal or external waveform bit",
        )


def _validate_extra_bytes_semantics(
    header: dict[str, Any],
    points: list[dict[str, Any]],
    vlrs: list[_DecodedRecord],
) -> None:
    point_format = _get_int(header, "point_data_record_format")
    actual_extra_bytes = (
        _get_int(header, "point_data_record_length") - FORMAT_MIN_POINT_LENGTH[point_format]
    )
    descriptors = [record for record in vlrs if record.kind == "extra_bytes"]
    if len(descriptors) > 1:
        raise LasError("invalid_document", "Extra Bytes records must not appear more than once")
    if descriptors and descriptors[0].described_extra_bytes > actual_extra_bytes:
        raise LasError(
            "invalid_document",
            "Extra Bytes VLR describes more extra bytes than are present in each point",
        )
    for point in points:
        payload = point.get("extra_bytes_b64")
        if actual_extra_bytes == 0 and payload is not None:
            raise LasError("invalid_document", "Unexpected extra bytes in point record")
        if actual_extra_bytes > 0:
            if not isinstance(payload, str):
                raise LasError(
                    "invalid_document", "Missing extra_bytes_b64 for point with extra bytes"
                )
            if (
                len(
                    _decode_base64_text(
                        payload,
                        "point.extra_bytes_b64",
                        error_code="invalid_document",
                    )
                )
                != actual_extra_bytes
            ):
                raise LasError(
                    "invalid_document",
                    "Point extra_bytes_b64 length does not match point record length",
                )


def _decode_extra_bytes_descriptor(data: bytes, *, offset: int) -> tuple[dict[str, Any], int]:
    if data[:2] != b"\x00\x00":
        raise LasError("invalid_document", "Extra Bytes reserved field must be zero", offset=offset)
    data_type = data[2]
    options = data[3]
    if not 0 <= data_type <= 30:
        raise LasError(
            "invalid_document", "Extra Bytes data_type must be between 0 and 30", offset=offset + 2
        )
    if data[36:40] != b"\x00\x00\x00\x00":
        raise LasError(
            "invalid_document", "Extra Bytes unused field must be zero", offset=offset + 36
        )
    name = _decode_padded_ascii(data[4:36], "extra_bytes.name", offset + 4)
    description = _decode_padded_ascii(data[160:192], "extra_bytes.description", offset + 160)
    no_data = _decode_extra_bytes_triplet(data_type, data[40:64])
    min_values = _decode_extra_bytes_triplet(data_type, data[64:88])
    max_values = _decode_extra_bytes_triplet(data_type, data[88:112])
    scale = list(struct.unpack("<3d", data[112:136]))
    offset_values = list(struct.unpack("<3d", data[136:160]))

    if data_type == 0:
        described_bytes = options
    else:
        described_bytes = _extra_bytes_storage_size(data_type)

    value_count = _extra_bytes_value_count(data_type)
    if value_count < 3:
        tail_indices = range(value_count, 3)
        if any(no_data[index] != 0 for index in tail_indices):
            raise LasError(
                "invalid_document",
                "Unused Extra Bytes no_data values must be zero",
                offset=offset + 40,
            )
        if any(min_values[index] != 0 for index in tail_indices):
            raise LasError(
                "invalid_document", "Unused Extra Bytes min values must be zero", offset=offset + 64
            )
        if any(max_values[index] != 0 for index in tail_indices):
            raise LasError(
                "invalid_document", "Unused Extra Bytes max values must be zero", offset=offset + 88
            )
        if any(scale[index] != 0.0 for index in tail_indices):
            raise LasError(
                "invalid_document",
                "Unused Extra Bytes scale values must be zero",
                offset=offset + 112,
            )
        if any(offset_values[index] != 0.0 for index in tail_indices):
            raise LasError(
                "invalid_document",
                "Unused Extra Bytes offset values must be zero",
                offset=offset + 136,
            )
    if data_type != 0:
        if options & ~0x1F:
            raise LasError(
                "invalid_document",
                "Extra Bytes options reserved bits must be zero",
                offset=offset + 3,
            )
        if not (options & 0x01) and any(value != 0 for value in no_data):
            raise LasError(
                "invalid_document",
                "Unused Extra Bytes no_data values must be zero",
                offset=offset + 40,
            )
        if not (options & 0x02) and any(value != 0 for value in min_values):
            raise LasError(
                "invalid_document", "Unused Extra Bytes min values must be zero", offset=offset + 64
            )
        if not (options & 0x04) and any(value != 0 for value in max_values):
            raise LasError(
                "invalid_document", "Unused Extra Bytes max values must be zero", offset=offset + 88
            )
        if not (options & 0x08) and any(value != 0.0 for value in scale):
            raise LasError(
                "invalid_document",
                "Unused Extra Bytes scale values must be zero",
                offset=offset + 112,
            )
        if not (options & 0x10) and any(value != 0.0 for value in offset_values):
            raise LasError(
                "invalid_document",
                "Unused Extra Bytes offset values must be zero",
                offset=offset + 136,
            )

    descriptor = {
        "data_type": data_type,
        "options": options,
        "name": name,
        "description": description,
        "no_data": no_data,
        "min": min_values,
        "max": max_values,
        "scale": scale,
        "offset": offset_values,
    }
    return descriptor, described_bytes


def _decode_extra_bytes_triplet(data_type: int, payload: bytes) -> list[int | float]:
    base_kind = _extra_bytes_base_kind(data_type)
    if base_kind == "float":
        return list(struct.unpack("<3d", payload))
    if base_kind == "unsigned":
        return list(struct.unpack("<3Q", payload))
    return list(struct.unpack("<3q", payload))


def _extra_bytes_base_kind(data_type: int) -> str:
    if data_type == 0:
        return "unsigned"
    if data_type in {1, 3, 5, 7, 11, 13, 15, 17, 21, 23, 25, 27}:
        return "unsigned"
    if data_type in {2, 4, 6, 8, 12, 14, 16, 18, 22, 24, 26, 28}:
        return "signed"
    if data_type in {9, 10, 19, 20, 29, 30}:
        return "float"
    raise LasError("invalid_document", "Unsupported Extra Bytes data_type")


def _extra_bytes_storage_size(data_type: int) -> int:
    sizes = {
        1: 1,
        2: 1,
        3: 2,
        4: 2,
        5: 4,
        6: 4,
        7: 8,
        8: 8,
        9: 4,
        10: 8,
        11: 2,
        12: 2,
        13: 4,
        14: 4,
        15: 8,
        16: 8,
        17: 16,
        18: 16,
        19: 8,
        20: 16,
        21: 3,
        22: 3,
        23: 6,
        24: 6,
        25: 12,
        26: 12,
        27: 24,
        28: 24,
        29: 12,
        30: 24,
    }
    return sizes[data_type]


def _extra_bytes_value_count(data_type: int) -> int:
    if data_type == 0:
        return 3
    if 1 <= data_type <= 10:
        return 1
    if 11 <= data_type <= 20:
        return 2
    return 3


def _decode_padded_ascii(raw: bytes, field_name: str, offset: int) -> str:
    if b"\x00" in raw:
        zero_index = raw.index(0)
        if any(value != 0 for value in raw[zero_index + 1 :]):
            raise LasError(
                "invalid_document",
                f"{field_name} has non-null data after a null terminator",
                offset=offset + zero_index,
            )
        trimmed = raw[:zero_index]
    else:
        trimmed = raw
    try:
        return trimmed.decode("ascii")
    except UnicodeDecodeError as exc:
        raise LasError(
            "invalid_document", f"{field_name} must contain ASCII text", offset=offset
        ) from exc


def _decode_ascii_blob(raw: bytes, field_name: str, offset: int) -> str:
    try:
        return raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise LasError(
            "invalid_document", f"{field_name} must contain ASCII text", offset=offset
        ) from exc


def _decode_null_terminated_ascii(raw: bytes, field_name: str, offset: int) -> str:
    if not raw or raw[-1] != 0:
        raise LasError("invalid_document", f"{field_name} must be null terminated", offset=offset)
    if any(value == 0 for value in raw[:-1]):
        raise LasError(
            "invalid_document", f"{field_name} contains an interior null byte", offset=offset
        )
    try:
        return raw[:-1].decode("ascii")
    except UnicodeDecodeError as exc:
        raise LasError(
            "invalid_document", f"{field_name} must contain ASCII text", offset=offset
        ) from exc


def _decode_null_terminated_utf8(raw: bytes, field_name: str, offset: int) -> str:
    if not raw or raw[-1] != 0:
        raise LasError("invalid_document", f"{field_name} must be null terminated", offset=offset)
    if any(value == 0 for value in raw[:-1]):
        raise LasError(
            "invalid_document", f"{field_name} contains an interior null byte", offset=offset
        )
    try:
        return raw[:-1].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LasError(
            "invalid_document", f"{field_name} must contain UTF-8 text", offset=offset
        ) from exc


def _encode_ascii(text: str, field_name: str) -> bytes:
    if "\x00" in text:
        raise LasError("invalid_request", f"{field_name} must not contain NUL bytes")
    return _encode_ascii_blob(text, field_name)


def _encode_ascii_blob(text: str, field_name: str) -> bytes:
    try:
        return text.encode("ascii")
    except UnicodeEncodeError as exc:
        raise LasError("invalid_request", f"{field_name} must contain ASCII text") from exc


def _encode_fixed_ascii(text: str, length: int, field_name: str) -> bytes:
    raw = _encode_ascii(text, field_name)
    if len(raw) > length:
        raise LasError("invalid_request", f"{field_name} exceeds {length} bytes")
    return raw + (b"\x00" * (length - len(raw)))


def _uuid_bytes_le(text: str, field_name: str) -> bytes:
    try:
        return uuid.UUID(text).bytes_le
    except ValueError as exc:
        raise LasError("invalid_request", f"{field_name} must be a valid UUID") from exc


def _coerce_number(value: Any, field_name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise LasError("invalid_request", f"{field_name} must be numeric")
    try:
        numeric = float(value)
    except OverflowError as exc:
        raise LasError("invalid_request", f"{field_name} must be finite") from exc
    if not math.isfinite(numeric):
        raise LasError("invalid_request", f"{field_name} must be finite")
    return numeric


def _get_int(mapping: dict[str, Any], key: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise LasError("invalid_request", f"{key} must be an integer")
    return value


def _get_int32(mapping: dict[str, Any], key: str) -> int:
    value = _get_int(mapping, key)
    if not (-0x80000000 <= value <= 0x7FFFFFFF):
        raise LasError("invalid_request", f"{key} must fit in int32")
    return value


def _get_uint8(mapping: dict[str, Any], key: str) -> int:
    value = _get_int(mapping, key)
    if not (0 <= value <= 0xFF):
        raise LasError("invalid_request", f"{key} must fit in uint8")
    return value


def _get_uint16(mapping: dict[str, Any], key: str) -> int:
    value = _get_int(mapping, key)
    if not (0 <= value <= 0xFFFF):
        raise LasError("invalid_request", f"{key} must fit in uint16")
    return value


def _get_uint32(mapping: dict[str, Any], key: str) -> int:
    value = _get_int(mapping, key)
    if not (0 <= value <= 0xFFFFFFFF):
        raise LasError("invalid_request", f"{key} must fit in uint32")
    return value


def _get_uint64(mapping: dict[str, Any], key: str) -> int:
    value = _get_int(mapping, key)
    if not (0 <= value <= 0xFFFFFFFFFFFFFFFF):
        raise LasError("invalid_request", f"{key} must fit in uint64")
    return value


def _get_number(mapping: dict[str, Any], key: str) -> float:
    return _coerce_number(mapping.get(key), key)


def _get_float32(mapping: dict[str, Any], key: str) -> float:
    value = _get_number(mapping, key)
    if not (-FLOAT32_MAX <= value <= FLOAT32_MAX):
        raise LasError("invalid_request", f"{key} must fit in float32")
    return value


def _get_str(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str):
        raise LasError("invalid_request", f"{key} must be a string")
    return value


def _get_bool(mapping: dict[str, Any], key: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise LasError("invalid_request", f"{key} must be a boolean")
    return value


def _ensure_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LasError("invalid_request", f"{field_name} must be an object")
    return cast(dict[str, Any], value)


def _ensure_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise LasError("invalid_request", f"{field_name} must be an array")
    return cast(list[Any], value)


def _ensure_uint32(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not (0 <= value <= 0xFFFFFFFF):
        raise LasError("invalid_request", f"{field_name} must fit in uint32")
    return value


def _ensure_uint64(value: Any, field_name: str) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not (0 <= value <= 0xFFFFFFFFFFFFFFFF)
    ):
        raise LasError("invalid_request", f"{field_name} must fit in uint64")
    return value


def _canonicalize_render_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    current = copy.deepcopy(dataset)
    header = _ensure_dict(current.get("header"), "dataset.header")
    vlrs = _ensure_list(current.get("vlrs"), "dataset.vlrs")
    points = _ensure_list(current.get("points"), "dataset.points")
    evlrs = _ensure_list(current.get("evlrs"), "dataset.evlrs")

    point_format = _get_int(header, "point_data_record_format")
    if point_format not in FORMAT_MIN_POINT_LENGTH:
        raise LasError(
            "invalid_request", "header.point_data_record_format must be between 0 and 10"
        )
    if _get_int(header, "version_major") != 1 or _get_int(header, "version_minor") != 4:
        raise LasError("invalid_request", "LAS render requests must use version 1.4")

    _render_validate(
        lambda: _validate_global_encoding(_get_int(header, "global_encoding"), header_offset=0)
    )

    rendered_vlrs = [_canonicalize_render_record(record, is_evlr=False) for record in vlrs]
    rendered_evlrs = [_canonicalize_render_record(record, is_evlr=True) for record in evlrs]

    point_bytes = [_encode_point_for_render(point, point_format=point_format) for point in points]
    point_record_lengths = {len(value) for value in point_bytes}
    if len(point_record_lengths) > 1:
        raise LasError(
            "invalid_request", "All points must have the same rendered point-record length"
        )
    point_record_length = (
        point_record_lengths.pop()
        if point_record_lengths
        else FORMAT_MIN_POINT_LENGTH[point_format]
    )

    if point_record_length < FORMAT_MIN_POINT_LENGTH[point_format]:
        raise LasError(
            "invalid_request",
            "Rendered point record length is smaller than the selected point format minimum",
        )

    offset_to_point_data = 375 + sum(54 + len(record.payload) for record in rendered_vlrs)
    point_data_size = sum(len(value) for value in point_bytes)
    first_evlr_offset = offset_to_point_data + point_data_size if rendered_evlrs else 0

    waveform_offset = 0
    running_evlr_offset = first_evlr_offset
    for record in rendered_evlrs:
        record.header_offset = running_evlr_offset
        if record.kind == "waveform_data_packets" and waveform_offset == 0:
            waveform_offset = running_evlr_offset
        running_evlr_offset += 60 + len(record.payload)

    typed_points = [cast(dict[str, Any], point) for point in points]
    coordinates = [_point_actual_coordinates(point, header) for point in typed_points]
    if coordinates:
        xs, ys, zs = zip(*coordinates, strict=True)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)
    else:
        min_x = max_x = min_y = max_y = min_z = max_z = 0.0

    legacy_mode = _maintains_legacy_compatibility(
        point_format=point_format,
        global_encoding=_get_int(header, "global_encoding"),
        evlrs=rendered_evlrs,
        point_count=len(point_bytes),
    )
    legacy_point_count = len(point_bytes) if legacy_mode else 0
    legacy_points_by_return = _counts_by_return(typed_points, 5) if legacy_mode else [0, 0, 0, 0, 0]

    header.update(
        {
            "header_size": 375,
            "offset_to_point_data": offset_to_point_data,
            "number_of_variable_length_records": len(rendered_vlrs),
            "point_data_record_length": point_record_length,
            "legacy_number_of_point_records": legacy_point_count,
            "legacy_number_of_points_by_return": legacy_points_by_return,
            "max_x": max_x,
            "min_x": min_x,
            "max_y": max_y,
            "min_y": min_y,
            "max_z": max_z,
            "min_z": min_z,
            "start_of_waveform_data_packet_record": waveform_offset,
            "start_of_first_extended_variable_length_record": first_evlr_offset,
            "number_of_extended_variable_length_records": len(rendered_evlrs),
            "number_of_point_records": len(point_bytes),
            "number_of_points_by_return": _counts_by_return(typed_points, 15),
        }
    )

    decoded_vlrs: list[_DecodedRecord] = []
    decoded_evlrs: list[_DecodedRecord] = []

    def decode_rendered_records() -> None:
        nonlocal decoded_vlrs, decoded_evlrs
        decoded_vlrs = _decode_rendered_records(rendered_vlrs, is_evlr=False)
        decoded_evlrs = _decode_rendered_records(rendered_evlrs, is_evlr=True)

    _render_validate(decode_rendered_records)
    _render_validate(lambda: _validate_crs(header, decoded_vlrs, decoded_evlrs))
    _render_validate(
        lambda: _validate_waveform_semantics(header, typed_points, decoded_vlrs, decoded_evlrs)
    )
    _render_validate(lambda: _validate_extra_bytes_semantics(header, typed_points, decoded_vlrs))

    return {
        "header": header,
        "_vlrs": rendered_vlrs,
        "_point_bytes": point_bytes,
        "_evlrs": rendered_evlrs,
    }


def _canonicalize_render_record(record: Any, *, is_evlr: bool) -> _RenderedRecord:
    record_dict = _ensure_dict(record, "record")
    user_id = _get_str(record_dict, "user_id")
    record_id = _get_uint16(record_dict, "record_id")
    description = _get_str(record_dict, "description") if "description" in record_dict else ""
    kind = _get_str(record_dict, "kind")
    described_extra_bytes = 0

    if kind == "opaque":
        data_b64 = _get_str(record_dict, "data_b64")
        payload = _decode_base64_text(data_b64, "opaque.data_b64")
    elif kind == "classification_lookup":
        if (user_id, record_id) != (LASF_SPEC, 0):
            raise LasError(
                "invalid_request", "classification_lookup records must use LASF_Spec / 0"
            )
        entries = _ensure_list(record_dict.get("entries", []), "classification_lookup.entries")
        descriptions = [""] * 256
        for entry in entries:
            entry_dict = _ensure_dict(entry, "classification_lookup entry")
            class_number = _get_int(entry_dict, "class_number")
            if not 0 <= class_number <= 255:
                raise LasError(
                    "invalid_request", "classification_lookup class_number must be 0..255"
                )
            descriptions[class_number] = _get_str(entry_dict, "description")
        payload_parts: list[bytes] = []
        for class_number, text in enumerate(descriptions):
            payload_parts.append(
                bytes([class_number])
                + _encode_fixed_ascii(text, 15, "classification_lookup.description")
            )
        payload = b"".join(payload_parts)
    elif kind == "text_area_description":
        if (user_id, record_id) != (LASF_SPEC, 3):
            raise LasError(
                "invalid_request", "text_area_description records must use LASF_Spec / 3"
            )
        payload = (
            _encode_ascii(_get_str(record_dict, "text"), "text_area_description.text") + b"\x00"
        )
    elif kind == "wkt_math_transform":
        if (user_id, record_id) != (LASF_PROJECTION, 2111):
            raise LasError(
                "invalid_request", "wkt_math_transform records must use LASF_Projection / 2111"
            )
        payload = _get_str(record_dict, "text").encode("utf-8") + b"\x00"
    elif kind == "wkt_coordinate_system":
        if (user_id, record_id) != (LASF_PROJECTION, 2112):
            raise LasError(
                "invalid_request", "wkt_coordinate_system records must use LASF_Projection / 2112"
            )
        payload = _get_str(record_dict, "text").encode("utf-8") + b"\x00"
    elif kind == "geo_key_directory":
        if (user_id, record_id) != (LASF_PROJECTION, 34735):
            raise LasError(
                "invalid_request", "geo_key_directory records must use LASF_Projection / 34735"
            )
        keys = _ensure_list(record_dict.get("keys", []), "geo_key_directory.keys")
        if len(keys) > 0xFFFF:
            raise LasError("invalid_request", "geo_key_directory.keys must fit in uint16 count")
        payload = struct.pack(
            "<4H",
            _get_uint16(record_dict, "key_directory_version"),
            _get_uint16(record_dict, "key_revision"),
            _get_uint16(record_dict, "minor_revision"),
            len(keys),
        )
        for key in keys:
            key_dict = _ensure_dict(key, "geo_key_directory key")
            payload += struct.pack(
                "<4H",
                _get_uint16(key_dict, "key_id"),
                _get_uint16(key_dict, "tiff_tag_location"),
                _get_uint16(key_dict, "count"),
                _get_uint16(key_dict, "value_offset"),
            )
    elif kind == "geo_double_params":
        if (user_id, record_id) != (LASF_PROJECTION, 34736):
            raise LasError(
                "invalid_request", "geo_double_params records must use LASF_Projection / 34736"
            )
        values = _ensure_list(record_dict.get("values", []), "geo_double_params.values")
        payload = b"".join(
            struct.pack("<d", _coerce_number(value, "geo_double_params.values[]"))
            for value in values
        )
    elif kind == "geo_ascii_params":
        if (user_id, record_id) != (LASF_PROJECTION, 34737):
            raise LasError(
                "invalid_request", "geo_ascii_params records must use LASF_Projection / 34737"
            )
        payload = _encode_ascii_blob(_get_str(record_dict, "text"), "geo_ascii_params.text")
    elif kind == "extra_bytes":
        if (user_id, record_id) != (LASF_SPEC, 4):
            raise LasError("invalid_request", "extra_bytes records must use LASF_Spec / 4")
        payload = b""
        descriptors = _ensure_list(record_dict.get("descriptors", []), "extra_bytes.descriptors")
        for descriptor_any in descriptors:
            descriptor_dict = _ensure_dict(descriptor_any, "extra_bytes descriptor")
            payload += _encode_extra_bytes_descriptor_for_render(descriptor_dict)
            data_type = _get_int(descriptor_dict, "data_type")
            described_extra_bytes += (
                _get_int(descriptor_dict, "options")
                if data_type == 0
                else _extra_bytes_storage_size(data_type)
            )
    elif kind == "waveform_packet_descriptor":
        if user_id != LASF_SPEC or not 100 <= record_id <= 354:
            raise LasError(
                "invalid_request",
                "waveform_packet_descriptor records must use LASF_Spec / 100..354",
            )
        payload = struct.pack(
            "<BBLLdd",
            _get_uint8(record_dict, "bits_per_sample"),
            _get_uint8(record_dict, "waveform_compression_type"),
            _get_uint32(record_dict, "number_of_samples"),
            _get_uint32(record_dict, "temporal_sample_spacing"),
            _get_number(record_dict, "digitizer_gain"),
            _get_number(record_dict, "digitizer_offset"),
        )
    elif kind == "waveform_data_packets":
        if not is_evlr:
            raise LasError("invalid_request", "waveform_data_packets must be placed in evlrs")
        if (user_id, record_id) != (LASF_SPEC, 65535):
            raise LasError(
                "invalid_request", "waveform_data_packets records must use LASF_Spec / 65535"
            )
        payload = _decode_base64_text(
            _get_str(record_dict, "data_b64"),
            "waveform_data_packets.data_b64",
        )
    elif kind == "superseded":
        if (user_id, record_id) != (LASF_SPEC, 7):
            raise LasError("invalid_request", "superseded records must use LASF_Spec / 7")
        payload = _decode_base64_text(
            _get_str(record_dict, "data_b64"),
            "superseded.data_b64",
        )
    else:
        raise LasError("invalid_request", f"Unsupported record kind: {kind}")

    if not is_evlr and len(payload) > 0xFFFF:
        raise LasError("invalid_request", "VLR payloads must fit in uint16 length")
    return _RenderedRecord(
        user_id=user_id,
        record_id=record_id,
        description=description,
        kind=kind,
        payload=payload,
        described_extra_bytes=described_extra_bytes if kind == "extra_bytes" else 0,
    )


def _encode_extra_bytes_descriptor_for_render(descriptor: dict[str, Any]) -> bytes:
    data_type = _get_uint8(descriptor, "data_type")
    options = _get_uint8(descriptor, "options")
    _validate_render_extra_bytes_data_type(data_type)
    name = _encode_fixed_ascii(_get_str(descriptor, "name"), 32, "extra_bytes.name")
    description = _encode_fixed_ascii(
        _get_str(descriptor, "description"),
        32,
        "extra_bytes.description",
    )
    no_data = _triplet_values(descriptor, "no_data")
    min_values = _triplet_values(descriptor, "min")
    max_values = _triplet_values(descriptor, "max")
    scale = _triplet_numbers(descriptor, "scale")
    offset = _triplet_numbers(descriptor, "offset")
    return (
        b"\x00\x00"
        + struct.pack("<B", data_type)
        + struct.pack("<B", options)
        + name
        + (b"\x00" * 4)
        + _encode_extra_bytes_triplet_for_render(data_type, no_data)
        + _encode_extra_bytes_triplet_for_render(data_type, min_values)
        + _encode_extra_bytes_triplet_for_render(data_type, max_values)
        + b"".join(struct.pack("<d", value) for value in scale)
        + b"".join(struct.pack("<d", value) for value in offset)
        + description
    )


def _encode_extra_bytes_triplet_for_render(data_type: int, values: list[Any]) -> bytes:
    if len(values) != 3:
        raise LasError(
            "invalid_request", "Extra Bytes triplet fields must contain exactly 3 values"
        )
    kind = _extra_bytes_base_kind(data_type)
    out = bytearray()
    for value in values:
        if kind == "float":
            out.extend(
                struct.pack("<d", _coerce_number(value, "Extra Bytes floating triplet value"))
            )
        elif kind == "unsigned":
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not (0 <= value <= 0xFFFFFFFFFFFFFFFF)
            ):
                raise LasError(
                    "invalid_request",
                    "Extra Bytes unsigned triplet values must fit in uint64",
                )
            out.extend(struct.pack("<Q", value))
        else:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not (-0x8000000000000000 <= value <= 0x7FFFFFFFFFFFFFFF)
            ):
                raise LasError(
                    "invalid_request", "Extra Bytes signed triplet values must fit in int64"
                )
            out.extend(struct.pack("<q", value))
    return bytes(out)


def _validate_render_extra_bytes_data_type(data_type: int) -> None:
    if data_type != 0 and not 1 <= data_type <= 30:
        raise LasError("invalid_request", "Unsupported Extra Bytes data_type")


def _triplet_values(mapping: dict[str, Any], key: str) -> list[Any]:
    values = _ensure_list(mapping.get(key), key)
    if len(values) != 3:
        raise LasError("invalid_request", f"{key} must be a 3-element array")
    return values


def _triplet_numbers(mapping: dict[str, Any], key: str) -> list[float]:
    values = _ensure_list(mapping.get(key), key)
    if len(values) != 3:
        raise LasError("invalid_request", f"{key} must be a 3-element array")
    return [
        _coerce_number(values[0], f"{key}[0]"),
        _coerce_number(values[1], f"{key}[1]"),
        _coerce_number(values[2], f"{key}[2]"),
    ]


def _encode_point_for_render(point_any: Any, *, point_format: int) -> bytes:
    if not isinstance(point_any, dict):
        raise LasError("invalid_request", "points entries must be objects")
    point = cast(dict[str, Any], point_any)
    raw = bytearray()
    raw.extend(
        struct.pack(
            "<iiiH",
            _get_int32(point, "x"),
            _get_int32(point, "y"),
            _get_int32(point, "z"),
            _get_uint16(point, "intensity"),
        )
    )
    if point_format in LEGACY_FORMATS:
        return_number = _get_int(point, "return_number")
        number_of_returns = _get_int(point, "number_of_returns")
        if not 1 <= return_number <= number_of_returns <= 5:
            raise LasError(
                "invalid_request", "Legacy return numbers must be in the range 1..5 and ordered"
            )
        scan_angle_rank = _get_int(point, "scan_angle_rank")
        if not -90 <= scan_angle_rank <= 90:
            raise LasError("invalid_request", "scan_angle_rank must be between -90 and 90")
        flags = (
            return_number
            | (number_of_returns << 3)
            | (int(_get_bool(point, "scan_direction_flag")) << 6)
            | (int(_get_bool(point, "edge_of_flight_line")) << 7)
        )
        classification = _get_int(point, "classification")
        if not 0 <= classification <= 31:
            raise LasError("invalid_request", "Legacy classification must be between 0 and 31")
        classification_byte = classification
        classification_byte |= int(_get_bool(point, "synthetic")) << 5
        classification_byte |= int(_get_bool(point, "key_point")) << 6
        classification_byte |= int(_get_bool(point, "withheld")) << 7
        raw.extend(
            struct.pack(
                "<BBbBH",
                flags,
                classification_byte,
                scan_angle_rank,
                _get_uint8(point, "user_data"),
                _get_uint16(point, "point_source_id"),
            )
        )
    else:
        return_number = _get_int(point, "return_number")
        number_of_returns = _get_int(point, "number_of_returns")
        if not 1 <= return_number <= number_of_returns <= 15:
            raise LasError(
                "invalid_request", "Modern return numbers must be between 1 and Number of Returns"
            )
        scan_angle = _get_int(point, "scan_angle")
        if not -30000 <= scan_angle <= 30000:
            raise LasError("invalid_request", "scan_angle must be between -30000 and 30000")
        scanner_channel = _get_int(point, "scanner_channel")
        if not 0 <= scanner_channel <= 3:
            raise LasError("invalid_request", "scanner_channel must be between 0 and 3")
        first_byte = return_number | (number_of_returns << 4)
        second_byte = (
            int(_get_bool(point, "synthetic"))
            | (int(_get_bool(point, "key_point")) << 1)
            | (int(_get_bool(point, "withheld")) << 2)
            | (int(_get_bool(point, "overlap")) << 3)
            | (scanner_channel << 4)
            | (int(_get_bool(point, "scan_direction_flag")) << 6)
            | (int(_get_bool(point, "edge_of_flight_line")) << 7)
        )
        raw.extend(
            struct.pack(
                "<BBBBhHd",
                first_byte,
                second_byte,
                _get_uint8(point, "classification"),
                _get_uint8(point, "user_data"),
                scan_angle,
                _get_uint16(point, "point_source_id"),
                _get_number(point, "gps_time"),
            )
        )
    if point_format in {1, 3, 4, 5}:
        raw.extend(struct.pack("<d", _get_number(point, "gps_time")))
    if point_format in COLOR_FORMATS:
        color_any = point.get("color")
        if not isinstance(color_any, dict):
            raise LasError("invalid_request", "color must be an object for this point format")
        color = cast(dict[str, Any], color_any)
        raw.extend(
            struct.pack(
                "<HHH",
                _get_uint16(color, "red"),
                _get_uint16(color, "green"),
                _get_uint16(color, "blue"),
            )
        )
    elif "color" in point:
        raise LasError("invalid_request", "color is not valid for this point format")
    if point_format in NIR_FORMATS:
        raw.extend(struct.pack("<H", _get_uint16(point, "nir")))
    elif "nir" in point:
        raise LasError("invalid_request", "nir is not valid for this point format")
    if point_format in WAVEFORM_FORMATS:
        waveform_any = point.get("waveform")
        if waveform_any is None:
            raw.extend(b"\x00" * 29)
        else:
            if not isinstance(waveform_any, dict):
                raise LasError("invalid_request", "waveform must be an object when present")
            waveform = cast(dict[str, Any], waveform_any)
            raw.extend(
                struct.pack(
                    "<BQLffff",
                    _get_uint8(waveform, "descriptor_index"),
                    _get_uint64(waveform, "byte_offset_to_waveform_data"),
                    _get_uint32(waveform, "waveform_packet_size_in_bytes"),
                    _get_float32(waveform, "return_point_waveform_location"),
                    _get_float32(waveform, "xt"),
                    _get_float32(waveform, "yt"),
                    _get_float32(waveform, "zt"),
                )
            )
    elif "waveform" in point:
        raise LasError("invalid_request", "waveform is not valid for this point format")

    extra_bytes_b64 = point.get("extra_bytes_b64")
    if extra_bytes_b64 is None:
        extra_bytes = b""
    elif isinstance(extra_bytes_b64, str):
        extra_bytes = _decode_base64_text(extra_bytes_b64, "extra_bytes_b64")
    else:
        raise LasError("invalid_request", "extra_bytes_b64 must be a base64 string")
    raw.extend(extra_bytes)
    return bytes(raw)


def _point_actual_coordinates(
    point: dict[str, Any], header: dict[str, Any]
) -> tuple[float, float, float]:
    return (
        (_get_int(point, "x") * _get_number(header, "x_scale_factor"))
        + _get_number(header, "x_offset"),
        (_get_int(point, "y") * _get_number(header, "y_scale_factor"))
        + _get_number(header, "y_offset"),
        (_get_int(point, "z") * _get_number(header, "z_scale_factor"))
        + _get_number(header, "z_offset"),
    )


def _counts_by_return(points: list[dict[str, Any]], size: int) -> list[int]:
    counts = [0] * size
    for point in points:
        return_number = _get_int(point, "return_number")
        if 1 <= return_number <= size:
            counts[return_number - 1] += 1
    return counts


def _render_validate(callback: Callable[[], None]) -> None:
    try:
        callback()
    except LasError as exc:
        if exc.code != "invalid_document":
            raise
        raise LasError("invalid_request", exc.message, offset=exc.offset) from exc


def _maintains_legacy_compatibility(
    *,
    point_format: int,
    global_encoding: int,
    evlrs: list[_RenderedRecord],
    point_count: int,
) -> bool:
    if point_format not in LEGACY_FORMATS:
        return False
    if point_count > 0xFFFFFFFF:
        return False
    if global_encoding & WKT_BIT:
        return False
    # LAS 1.4 lets writers decide whether to preserve legacy counters. The
    # reference uses the conservative policy that any EVLR disables them.
    if evlrs:
        return False
    return True


def _decode_rendered_records(
    records: list[_RenderedRecord], *, is_evlr: bool
) -> list[_DecodedRecord]:
    return [_to_decoded(record, is_evlr=is_evlr) for record in records]


def _to_decoded(record: _RenderedRecord, *, is_evlr: bool) -> _DecodedRecord:
    decoded = _decode_record(
        user_id=record.user_id,
        record_id=record.record_id,
        description=record.description,
        payload=record.payload,
        payload_offset=0,
        is_evlr=is_evlr,
    )
    decoded.header_offset = record.header_offset
    return decoded


@dataclass(slots=True)
class _DecodedRecord:
    record: dict[str, Any]
    kind: str
    payload: bytes
    described_extra_bytes: int = 0
    header_offset: int = 0

    @property
    def record_id(self) -> int:
        return _get_int(self.record, "record_id")


@dataclass(slots=True)
class _RenderedRecord:
    user_id: str
    record_id: int
    description: str
    kind: str
    payload: bytes
    described_extra_bytes: int = 0
    header_offset: int = 0

    def as_dict(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "user_id": self.user_id,
            "record_id": self.record_id,
            "description": self.description,
            "kind": self.kind,
        }
        if self.kind in {"opaque", "waveform_data_packets"}:
            record["data_b64"] = base64.b64encode(self.payload).decode("ascii")
        return record
