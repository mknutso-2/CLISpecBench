from __future__ import annotations

import base64
import copy
import struct
import uuid
from typing import Any, cast

FORMAT_MIN_POINT_LENGTH: dict[int, int] = {
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

LEGACY_FORMATS = {0, 1, 2, 3, 4, 5}
MODERN_FORMATS = {6, 7, 8, 9, 10}
GPS_TIME_FORMATS = {1, 3, 4, 5, 6, 7, 8, 9, 10}
COLOR_FORMATS = {2, 3, 5, 7, 8, 10}
NIR_FORMATS = {8, 10}
WAVEFORM_FORMATS = {4, 5, 9, 10}

LASF_PROJECTION = "LASF_Projection"
LASF_SPEC = "LASF_Spec"

WKT_BIT = 1 << 4
WAVEFORM_INTERNAL_BIT = 1 << 1
WAVEFORM_EXTERNAL_BIT = 1 << 2
EXTRA_BYTES_STORAGE_SIZE: dict[int, int] = {
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


def clone(value: Any) -> Any:
    return copy.deepcopy(value)


def b64encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64decode_text(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"), validate=True)


def uuid_string() -> str:
    return "123e4567-e89b-12d3-a456-426614174000"


def _f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def default_header(point_format: int, *, global_encoding: int) -> dict[str, Any]:
    return {
        "file_source_id": 7,
        "global_encoding": global_encoding,
        "project_id": uuid_string(),
        "version_major": 1,
        "version_minor": 4,
        "system_identifier": "OTHER",
        "generating_software": "LASFixture 1.0",
        "file_creation_day_of_year": 42,
        "file_creation_year": 2026,
        "point_data_record_format": point_format,
        "x_scale_factor": 0.01,
        "y_scale_factor": 0.01,
        "z_scale_factor": 0.01,
        "x_offset": 1000.0,
        "y_offset": 2000.0,
        "z_offset": 50.0,
    }


def geo_key_directory_vlr() -> dict[str, Any]:
    return {
        "user_id": LASF_PROJECTION,
        "record_id": 34735,
        "description": "GeoKeys",
        "kind": "geo_key_directory",
        "key_directory_version": 1,
        "key_revision": 1,
        "minor_revision": 0,
        "keys": [
            {
                "key_id": 1024,
                "tiff_tag_location": 0,
                "count": 1,
                "value_offset": 2,
            },
            {
                "key_id": 3072,
                "tiff_tag_location": 0,
                "count": 1,
                "value_offset": 32615,
            },
        ],
    }


def geo_double_params_vlr() -> dict[str, Any]:
    return {
        "user_id": LASF_PROJECTION,
        "record_id": 34736,
        "description": "GeoDoubles",
        "kind": "geo_double_params",
        "values": [123.5, 456.25],
    }


def geo_ascii_params_vlr() -> dict[str, Any]:
    return {
        "user_id": LASF_PROJECTION,
        "record_id": 34737,
        "description": "GeoASCII",
        "kind": "geo_ascii_params",
        "text": "EPSG:32615|WGS 84 / UTM zone 15N|\u0000",
    }


def wkt_coordinate_system_vlr(*, evlr: bool = False) -> dict[str, Any]:
    return {
        "user_id": LASF_PROJECTION,
        "record_id": 2112,
        "description": "WKT CRS",
        "kind": "wkt_coordinate_system",
        "text": 'PROJCS["WGS 84 / UTM zone 15N",GEOGCS["WGS 84"]]',
        "_evlr_hint": evlr,
    }


def wkt_math_transform_vlr(*, evlr: bool = False) -> dict[str, Any]:
    return {
        "user_id": LASF_PROJECTION,
        "record_id": 2111,
        "description": "WKT Math",
        "kind": "wkt_math_transform",
        "text": 'PARAM_MT["Affine",PARAMETER["A0",1.0]]',
        "_evlr_hint": evlr,
    }


def classification_lookup_vlr() -> dict[str, Any]:
    return {
        "user_id": LASF_SPEC,
        "record_id": 0,
        "description": "ClassLookup",
        "kind": "classification_lookup",
        "entries": [
            {"class_number": 2, "description": "Ground"},
            {"class_number": 9, "description": "Water"},
        ],
    }


def text_area_description_vlr() -> dict[str, Any]:
    return {
        "user_id": LASF_SPEC,
        "record_id": 3,
        "description": "TextArea",
        "kind": "text_area_description",
        "text": "Synthetic fixture",
    }


def extra_bytes_vlr() -> dict[str, Any]:
    return {
        "user_id": LASF_SPEC,
        "record_id": 4,
        "description": "ExtraBytes",
        "kind": "extra_bytes",
        "descriptors": [
            {
                "data_type": 3,
                "options": 0x04,
                "name": "reflectivity",
                "description": "Normalized reflectivity",
                "no_data": [0, 0, 0],
                "min": [0, 0, 0],
                "max": [5000, 0, 0],
                "scale": [0.0, 0.0, 0.0],
                "offset": [0.0, 0.0, 0.0],
            }
        ],
    }


def extra_bytes_vlr_for_type(data_type: int, *, options: int = 0) -> dict[str, Any]:
    return {
        "user_id": LASF_SPEC,
        "record_id": 4,
        "description": f"Extra{data_type}",
        "kind": "extra_bytes",
        "descriptors": [
            {
                "data_type": data_type,
                "options": options,
                "name": f"extra_{data_type}",
                "description": f"Extra bytes type {data_type}",
                "no_data": [0, 0, 0],
                "min": [0, 0, 0],
                "max": [0, 0, 0],
                "scale": [0.0, 0.0, 0.0],
                "offset": [0.0, 0.0, 0.0],
            }
        ],
    }


def undocumented_extra_bytes_vlr(byte_count: int) -> dict[str, Any]:
    return {
        "user_id": LASF_SPEC,
        "record_id": 4,
        "description": "Undocumented",
        "kind": "extra_bytes",
        "descriptors": [
            {
                "data_type": 0,
                "options": byte_count,
                "name": "undocumented",
                "description": "Undocumented bytes",
                "no_data": [0, 0, 0],
                "min": [0, 0, 0],
                "max": [0, 0, 0],
                "scale": [0.0, 0.0, 0.0],
                "offset": [0.0, 0.0, 0.0],
            }
        ],
    }


def waveform_packet_descriptor_vlr(record_id: int = 100) -> dict[str, Any]:
    return {
        "user_id": LASF_SPEC,
        "record_id": record_id,
        "description": "WaveDesc",
        "kind": "waveform_packet_descriptor",
        "bits_per_sample": 16,
        "waveform_compression_type": 0,
        "number_of_samples": 3,
        "temporal_sample_spacing": 1000,
        "digitizer_gain": 0.5,
        "digitizer_offset": 1.25,
    }


def waveform_data_packets_evlr(data: bytes | None = None) -> dict[str, Any]:
    payload = b"\x01\x02\x03\x04" if data is None else data
    return {
        "user_id": LASF_SPEC,
        "record_id": 65535,
        "description": "WaveData",
        "kind": "waveform_data_packets",
        "data_b64": b64encode_bytes(payload),
    }


def opaque_vlr(
    user_id: str,
    record_id: int,
    data: bytes,
    *,
    description: str = "",
) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "record_id": record_id,
        "description": description,
        "kind": "opaque",
        "data_b64": b64encode_bytes(data),
    }


def point_for_format(point_format: int, *, extra_bytes: bytes = b"") -> dict[str, Any]:
    point: dict[str, Any] = {
        "x": 100 + point_format,
        "y": 200 + point_format,
        "z": 300 + point_format,
        "intensity": 10 + point_format,
        "return_number": 1,
        "number_of_returns": 1,
        "scan_direction_flag": bool(point_format % 2),
        "edge_of_flight_line": False,
        "classification": 2 if point_format in LEGACY_FORMATS else 17,
        "user_data": point_format,
        "point_source_id": 7,
    }
    if point_format in LEGACY_FORMATS:
        point.update(
            {
                "synthetic": False,
                "key_point": point_format == 0,
                "withheld": False,
                "scan_angle_rank": -5 + point_format,
            }
        )
    else:
        point.update(
            {
                "synthetic": False,
                "key_point": False,
                "withheld": False,
                "overlap": point_format == 6,
                "scanner_channel": point_format % 4,
                "scan_angle": 100 * point_format,
                "gps_time": 1000.25 + point_format,
            }
        )
    if point_format in GPS_TIME_FORMATS and point_format in LEGACY_FORMATS:
        point["gps_time"] = 1000.25 + point_format
    if point_format in COLOR_FORMATS:
        point["color"] = {
            "red": 1000 + point_format,
            "green": 2000 + point_format,
            "blue": 3000 + point_format,
        }
    if point_format in NIR_FORMATS:
        point["nir"] = 4000 + point_format
    if point_format in WAVEFORM_FORMATS:
        point["waveform"] = {
            "descriptor_index": 1,
            "byte_offset_to_waveform_data": 2,
            "waveform_packet_size_in_bytes": 4,
            "return_point_waveform_location": 8.5,
            "xt": _f32(0.1),
            "yt": _f32(-0.2),
            "zt": _f32(0.3),
        }
    if extra_bytes:
        point["extra_bytes_b64"] = b64encode_bytes(extra_bytes)
    return point


def dataset_for_point_format(point_format: int) -> dict[str, Any]:
    if point_format in LEGACY_FORMATS:
        vlrs: list[dict[str, Any]] = [geo_key_directory_vlr()]
        global_encoding = 0
    else:
        vlrs = [wkt_coordinate_system_vlr()]
        global_encoding = WKT_BIT
    evlrs: list[dict[str, Any]] = []
    if point_format in WAVEFORM_FORMATS:
        global_encoding |= WAVEFORM_INTERNAL_BIT
        vlrs.append(waveform_packet_descriptor_vlr())
        evlrs.append(waveform_data_packets_evlr())
    return {
        "header": default_header(point_format, global_encoding=global_encoding),
        "vlrs": vlrs,
        "points": [point_for_format(point_format)],
        "evlrs": evlrs,
    }


def dataset_with_extra_bytes(point_format: int) -> dict[str, Any]:
    dataset = dataset_for_point_format(point_format)
    dataset["vlrs"].append(extra_bytes_vlr())
    dataset["points"] = [point_for_format(point_format, extra_bytes=b"\x34\x12")]
    return dataset


def dataset_with_extra_bytes_type(data_type: int, *, options: int = 0) -> dict[str, Any]:
    dataset = dataset_for_point_format(6)
    dataset["vlrs"].append(extra_bytes_vlr_for_type(data_type, options=options))
    payload_size = options if data_type == 0 else EXTRA_BYTES_STORAGE_SIZE[data_type]
    dataset["points"] = [point_for_format(6, extra_bytes=bytes(range(payload_size)))]
    return dataset


def dataset_without_waveform_packets(point_format: int) -> dict[str, Any]:
    dataset = dataset_for_point_format(point_format)
    dataset["header"]["global_encoding"] &= ~(WAVEFORM_INTERNAL_BIT | WAVEFORM_EXTERNAL_BIT)
    dataset["vlrs"] = [
        record for record in dataset["vlrs"] if record.get("kind") != "waveform_packet_descriptor"
    ]
    dataset["evlrs"] = []
    for point in dataset["points"]:
        point.pop("waveform", None)
    return dataset


def dataset_with_external_waveform_packets() -> dict[str, Any]:
    dataset = dataset_for_point_format(9)
    dataset["header"]["global_encoding"] &= ~WAVEFORM_INTERNAL_BIT
    dataset["header"]["global_encoding"] |= WAVEFORM_EXTERNAL_BIT
    dataset["evlrs"] = []
    return dataset


def dataset_with_multiple_evlrs() -> dict[str, Any]:
    dataset = dataset_for_point_format(6)
    dataset["evlrs"] = [
        opaque_vlr("TEST_USER", 88, b"\x10\x11", description="EVLR-A"),
        opaque_vlr("TEST_USER", 89, b"\x12\x13\x14", description="EVLR-B"),
    ]
    return dataset


def dataset_with_legacy_multi_returns() -> dict[str, Any]:
    dataset = dataset_for_point_format(0)
    first = point_for_format(0)
    second = point_for_format(0)
    second["x"] = 101
    second["return_number"] = 2
    second["number_of_returns"] = 2
    dataset["points"] = [first, second]
    return dataset


def dataset_with_modern_multi_returns() -> dict[str, Any]:
    dataset = dataset_for_point_format(6)
    first = point_for_format(6)
    second = point_for_format(6)
    third = point_for_format(6)
    second["x"] = 107
    second["return_number"] = 2
    second["number_of_returns"] = 3
    third["x"] = 108
    third["return_number"] = 3
    third["number_of_returns"] = 3
    dataset["points"] = [first, second, third]
    return dataset


def dataset_with_classification_lookup() -> dict[str, Any]:
    dataset = dataset_for_point_format(0)
    dataset["vlrs"] = [
        geo_key_directory_vlr(),
        classification_lookup_vlr(),
        text_area_description_vlr(),
    ]
    return dataset


def dataset_with_geotiff_triplet() -> dict[str, Any]:
    dataset = dataset_for_point_format(0)
    dataset["vlrs"] = [
        geo_key_directory_vlr(),
        geo_double_params_vlr(),
        geo_ascii_params_vlr(),
    ]
    return dataset


def dataset_with_wkt_pair() -> dict[str, Any]:
    dataset = dataset_for_point_format(6)
    dataset["vlrs"] = [wkt_math_transform_vlr(), wkt_coordinate_system_vlr()]
    return dataset


def dataset_with_unknown_records() -> dict[str, Any]:
    dataset = dataset_for_point_format(6)
    dataset["vlrs"].append(opaque_vlr("TEST_USER", 77, b"\x00\x01\x02", description="Opaque"))
    dataset["evlrs"].append(
        opaque_vlr("TEST_USER", 88, b"\x10\x11\x12\x13", description="OpaqueEVLR")
    )
    return dataset


def _ensure_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    return value


def _ensure_number(value: Any, field_name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be numeric")
    return float(value)


def _ensure_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be boolean")
    return value


def _ensure_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value


def _encode_fixed_ascii(text: str, length: int, field_name: str) -> bytes:
    raw = _ensure_string(text, field_name).encode("ascii")
    if len(raw) > length:
        raise ValueError(f"{field_name} exceeds {length} bytes")
    return raw + (b"\x00" * (length - len(raw)))


def _encode_fixed_utf8_null_terminated(text: str, field_name: str) -> bytes:
    raw = _ensure_string(text, field_name).encode("utf-8")
    return raw + b"\x00"


def _encode_fixed_ascii_null_terminated(text: str, field_name: str) -> bytes:
    raw = _ensure_string(text, field_name).encode("ascii")
    return raw + b"\x00"


def _project_id_bytes(project_id: str) -> bytes:
    return uuid.UUID(_ensure_string(project_id, "project_id")).bytes_le


def _extra_bytes_length(point_format: int, point: dict[str, Any]) -> int:
    extra = point.get("extra_bytes_b64")
    if extra is None:
        return 0
    return len(b64decode_text(_ensure_string(extra, "point.extra_bytes_b64")))


def _counts_by_return(points: list[dict[str, Any]], size: int) -> list[int]:
    counts = [0] * size
    for point in points:
        return_number = _ensure_int(point["return_number"], "point.return_number")
        if 1 <= return_number <= size:
            counts[return_number - 1] += 1
    return counts


def _maintains_legacy_compatibility(dataset: dict[str, Any], point_count: int) -> bool:
    header = cast(dict[str, Any], dataset["header"])
    point_format = _ensure_int(
        header["point_data_record_format"],
        "header.point_data_record_format",
    )
    if point_format not in LEGACY_FORMATS:
        return False
    if point_count > 0xFFFFFFFF:
        return False
    global_encoding = _ensure_int(header["global_encoding"], "header.global_encoding")
    if global_encoding & WKT_BIT:
        return False
    evlrs = cast(list[dict[str, Any]], dataset["evlrs"])
    if evlrs:
        return False
    return True


def _point_actual_coordinates(
    point: dict[str, Any],
    header: dict[str, Any],
) -> tuple[float, float, float]:
    return (
        (_ensure_int(point["x"], "point.x") * _ensure_number(header["x_scale_factor"], "x_scale"))
        + _ensure_number(header["x_offset"], "x_offset"),
        (_ensure_int(point["y"], "point.y") * _ensure_number(header["y_scale_factor"], "y_scale"))
        + _ensure_number(header["y_offset"], "y_offset"),
        (_ensure_int(point["z"], "point.z") * _ensure_number(header["z_scale_factor"], "z_scale"))
        + _ensure_number(header["z_offset"], "z_offset"),
    )


def _normalized_extra_descriptor(descriptor: dict[str, Any]) -> dict[str, Any]:
    current = clone(descriptor)
    for key in ("no_data", "min", "max", "scale", "offset"):
        values = list(cast(list[Any], current.get(key, [0, 0, 0])))
        if len(values) != 3:
            raise ValueError(f"extra-bytes descriptor {key} must have 3 values")
        current[key] = values
    return current


def _canonical_record_payload(
    record: dict[str, Any],
    *,
    is_evlr: bool,
) -> tuple[dict[str, Any], bytes]:
    current = clone(record)
    current.pop("_evlr_hint", None)
    user_id = _ensure_string(current["user_id"], "record.user_id")
    record_id = _ensure_int(current["record_id"], "record.record_id")
    description = _ensure_string(current.get("description", ""), "record.description")
    kind = _ensure_string(current["kind"], "record.kind")

    if kind == "opaque":
        payload = b64decode_text(_ensure_string(current["data_b64"], "record.data_b64"))
    elif kind == "classification_lookup":
        if (user_id, record_id) != (LASF_SPEC, 0):
            raise ValueError("classification_lookup records must use LASF_Spec / 0")
        entries = {
            _ensure_int(entry["class_number"], "entry.class_number"): _ensure_string(
                entry["description"], "entry.description"
            )
            for entry in cast(list[dict[str, Any]], current.get("entries", []))
        }
        payload_parts: list[bytes] = []
        ordered_entries: list[dict[str, Any]] = []
        for class_number in sorted(entries):
            if not 0 <= class_number <= 255:
                raise ValueError("classification_lookup class_number out of range")
            ordered_entries.append(
                {"class_number": class_number, "description": entries[class_number]}
            )
        current["entries"] = ordered_entries
        for class_number in range(256):
            description_text = entries.get(class_number, "")
            description_bytes = _encode_fixed_ascii(
                description_text,
                15,
                "classification description",
            )
            payload_parts.append(bytes([class_number]) + description_bytes)
        payload = b"".join(payload_parts)
    elif kind == "text_area_description":
        if (user_id, record_id) != (LASF_SPEC, 3):
            raise ValueError("text_area_description records must use LASF_Spec / 3")
        payload = _encode_fixed_ascii_null_terminated(current["text"], "record.text")
    elif kind == "wkt_math_transform":
        if (user_id, record_id) != (LASF_PROJECTION, 2111):
            raise ValueError("wkt_math_transform records must use LASF_Projection / 2111")
        payload = _encode_fixed_utf8_null_terminated(current["text"], "record.text")
    elif kind == "wkt_coordinate_system":
        if (user_id, record_id) != (LASF_PROJECTION, 2112):
            raise ValueError("wkt_coordinate_system records must use LASF_Projection / 2112")
        payload = _encode_fixed_utf8_null_terminated(current["text"], "record.text")
    elif kind == "geo_key_directory":
        if (user_id, record_id) != (LASF_PROJECTION, 34735):
            raise ValueError("geo_key_directory records must use LASF_Projection / 34735")
        keys = cast(list[dict[str, Any]], current.get("keys", []))
        payload = struct.pack(
            "<4H",
            _ensure_int(current["key_directory_version"], "key_directory_version"),
            _ensure_int(current["key_revision"], "key_revision"),
            _ensure_int(current["minor_revision"], "minor_revision"),
            len(keys),
        ) + b"".join(
            struct.pack(
                "<4H",
                _ensure_int(key["key_id"], "key_id"),
                _ensure_int(key["tiff_tag_location"], "tiff_tag_location"),
                _ensure_int(key["count"], "count"),
                _ensure_int(key["value_offset"], "value_offset"),
            )
            for key in keys
        )
    elif kind == "geo_double_params":
        if (user_id, record_id) != (LASF_PROJECTION, 34736):
            raise ValueError("geo_double_params records must use LASF_Projection / 34736")
        values = cast(list[Any], current.get("values", []))
        payload = b"".join(
            struct.pack("<d", _ensure_number(value, "geo_double value")) for value in values
        )
    elif kind == "geo_ascii_params":
        if (user_id, record_id) != (LASF_PROJECTION, 34737):
            raise ValueError("geo_ascii_params records must use LASF_Projection / 34737")
        payload = _ensure_string(current["text"], "record.text").encode("ascii")
    elif kind == "extra_bytes":
        if (user_id, record_id) != (LASF_SPEC, 4):
            raise ValueError("extra_bytes records must use LASF_Spec / 4")
        descriptors = [
            _normalized_extra_descriptor(descriptor)
            for descriptor in cast(list[dict[str, Any]], current.get("descriptors", []))
        ]
        current["descriptors"] = descriptors
        payload = b"".join(_encode_extra_bytes_descriptor(descriptor) for descriptor in descriptors)
    elif kind == "waveform_packet_descriptor":
        if user_id != LASF_SPEC or not (100 <= record_id <= 354):
            raise ValueError("waveform_packet_descriptor record_id must be in 100..354")
        payload = struct.pack(
            "<BBLLdd",
            _ensure_int(current["bits_per_sample"], "bits_per_sample"),
            _ensure_int(current["waveform_compression_type"], "waveform_compression_type"),
            _ensure_int(current["number_of_samples"], "number_of_samples"),
            _ensure_int(current["temporal_sample_spacing"], "temporal_sample_spacing"),
            _ensure_number(current["digitizer_gain"], "digitizer_gain"),
            _ensure_number(current["digitizer_offset"], "digitizer_offset"),
        )
    elif kind == "waveform_data_packets":
        if not is_evlr:
            raise ValueError("waveform_data_packets must be placed in evlrs")
        if (user_id, record_id) != (LASF_SPEC, 65535):
            raise ValueError("waveform_data_packets records must use LASF_Spec / 65535")
        payload = b64decode_text(_ensure_string(current["data_b64"], "record.data_b64"))
    else:
        raise ValueError(f"unsupported record kind: {kind}")

    current["user_id"] = user_id
    current["record_id"] = record_id
    current["description"] = description
    current["kind"] = kind
    return current, payload


def _encode_extra_bytes_descriptor(descriptor: dict[str, Any]) -> bytes:
    data_type = _ensure_int(descriptor["data_type"], "descriptor.data_type")
    options = _ensure_int(descriptor["options"], "descriptor.options")
    name = _encode_fixed_ascii(
        _ensure_string(descriptor["name"], "descriptor.name"),
        32,
        "descriptor.name",
    )
    description = _encode_fixed_ascii(
        _ensure_string(descriptor["description"], "descriptor.description"),
        32,
        "descriptor.description",
    )
    no_data = cast(list[Any], descriptor["no_data"])
    min_values = cast(list[Any], descriptor["min"])
    max_values = cast(list[Any], descriptor["max"])
    scale = cast(list[Any], descriptor["scale"])
    offset = cast(list[Any], descriptor["offset"])

    return (
        b"\x00\x00"
        + struct.pack("<B", data_type)
        + struct.pack("<B", options)
        + name
        + (b"\x00" * 4)
        + _encode_extra_bytes_triplet(data_type, no_data)
        + _encode_extra_bytes_triplet(data_type, min_values)
        + _encode_extra_bytes_triplet(data_type, max_values)
        + b"".join(struct.pack("<d", _ensure_number(value, "descriptor.scale")) for value in scale)
        + b"".join(
            struct.pack("<d", _ensure_number(value, "descriptor.offset")) for value in offset
        )
        + description
    )


def _encode_extra_bytes_triplet(data_type: int, values: list[Any]) -> bytes:
    base_kind = _extra_bytes_base_kind(data_type)
    encoded = bytearray()
    for value in values:
        if base_kind == "float":
            encoded.extend(struct.pack("<d", _ensure_number(value, "extra_bytes_triplet")))
        elif base_kind == "unsigned":
            encoded.extend(struct.pack("<Q", _ensure_int(value, "extra_bytes_triplet")))
        else:
            encoded.extend(struct.pack("<q", _ensure_int(value, "extra_bytes_triplet")))
    return bytes(encoded)


def _extra_bytes_base_kind(data_type: int) -> str:
    if data_type == 0:
        return "unsigned"
    if data_type in {1, 3, 5, 7, 11, 13, 15, 17, 21, 23, 25, 27}:
        return "unsigned"
    if data_type in {2, 4, 6, 8, 12, 14, 16, 18, 22, 24, 26, 28}:
        return "signed"
    if data_type in {9, 10, 19, 20, 29, 30}:
        return "float"
    raise ValueError(f"unsupported extra-bytes data_type: {data_type}")


def _point_bytes(point_format: int, point: dict[str, Any]) -> bytes:
    common = bytearray()
    common.extend(
        struct.pack(
            "<iiiH",
            _ensure_int(point["x"], "point.x"),
            _ensure_int(point["y"], "point.y"),
            _ensure_int(point["z"], "point.z"),
            _ensure_int(point["intensity"], "point.intensity"),
        )
    )
    if point_format in LEGACY_FORMATS:
        return_bits = _ensure_int(point["return_number"], "point.return_number")
        number_bits = _ensure_int(point["number_of_returns"], "point.number_of_returns")
        legacy_flags = (
            return_bits
            | (number_bits << 3)
            | (int(_ensure_bool(point["scan_direction_flag"], "point.scan_direction_flag")) << 6)
            | (int(_ensure_bool(point["edge_of_flight_line"], "point.edge_of_flight_line")) << 7)
        )
        classification = _ensure_int(point["classification"], "point.classification") & 0x1F
        classification |= int(_ensure_bool(point["synthetic"], "point.synthetic")) << 5
        classification |= int(_ensure_bool(point["key_point"], "point.key_point")) << 6
        classification |= int(_ensure_bool(point["withheld"], "point.withheld")) << 7
        common.extend(
            struct.pack(
                "<BBbBH",
                legacy_flags,
                classification,
                _ensure_int(point["scan_angle_rank"], "point.scan_angle_rank"),
                _ensure_int(point["user_data"], "point.user_data"),
                _ensure_int(point["point_source_id"], "point.point_source_id"),
            )
        )
    else:
        first_byte = _ensure_int(point["return_number"], "point.return_number") | (
            _ensure_int(point["number_of_returns"], "point.number_of_returns") << 4
        )
        second_byte = (
            int(_ensure_bool(point["synthetic"], "point.synthetic"))
            | (int(_ensure_bool(point["key_point"], "point.key_point")) << 1)
            | (int(_ensure_bool(point["withheld"], "point.withheld")) << 2)
            | (int(_ensure_bool(point["overlap"], "point.overlap")) << 3)
            | (_ensure_int(point["scanner_channel"], "point.scanner_channel") << 4)
            | (int(_ensure_bool(point["scan_direction_flag"], "point.scan_direction_flag")) << 6)
            | (int(_ensure_bool(point["edge_of_flight_line"], "point.edge_of_flight_line")) << 7)
        )
        common.extend(
            struct.pack(
                "<BBBBhHd",
                first_byte,
                second_byte,
                _ensure_int(point["classification"], "point.classification"),
                _ensure_int(point["user_data"], "point.user_data"),
                _ensure_int(point["scan_angle"], "point.scan_angle"),
                _ensure_int(point["point_source_id"], "point.point_source_id"),
                _ensure_number(point["gps_time"], "point.gps_time"),
            )
        )
    if point_format in {1, 3, 4, 5}:
        common.extend(struct.pack("<d", _ensure_number(point["gps_time"], "point.gps_time")))
    if point_format in COLOR_FORMATS:
        color = cast(dict[str, Any], point["color"])
        common.extend(
            struct.pack(
                "<HHH",
                _ensure_int(color["red"], "point.color.red"),
                _ensure_int(color["green"], "point.color.green"),
                _ensure_int(color["blue"], "point.color.blue"),
            )
        )
    if point_format in NIR_FORMATS:
        common.extend(struct.pack("<H", _ensure_int(point["nir"], "point.nir")))
    if point_format in WAVEFORM_FORMATS:
        waveform = cast(dict[str, Any] | None, point.get("waveform"))
        if waveform is None:
            common.extend(b"\x00" * 29)
        else:
            common.extend(
                struct.pack(
                    "<BQ Lf fff".replace(" ", ""),
                    _ensure_int(waveform["descriptor_index"], "waveform.descriptor_index"),
                    _ensure_int(
                        waveform["byte_offset_to_waveform_data"],
                        "waveform.byte_offset_to_waveform_data",
                    ),
                    _ensure_int(
                        waveform["waveform_packet_size_in_bytes"],
                        "waveform.waveform_packet_size_in_bytes",
                    ),
                    _ensure_number(
                        waveform["return_point_waveform_location"],
                        "waveform.return_point_waveform_location",
                    ),
                    _ensure_number(waveform["xt"], "waveform.xt"),
                    _ensure_number(waveform["yt"], "waveform.yt"),
                    _ensure_number(waveform["zt"], "waveform.zt"),
                )
            )
    extra_bytes = b""
    if "extra_bytes_b64" in point:
        extra_bytes = b64decode_text(
            _ensure_string(point["extra_bytes_b64"], "point.extra_bytes_b64")
        )
    return bytes(common) + extra_bytes


def canonical_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    header = clone(cast(dict[str, Any], dataset["header"]))
    points = [clone(point) for point in cast(list[dict[str, Any]], dataset["points"])]
    vlrs = [clone(record) for record in cast(list[dict[str, Any]], dataset["vlrs"])]
    evlrs = [clone(record) for record in cast(list[dict[str, Any]], dataset["evlrs"])]

    point_format = _ensure_int(
        header["point_data_record_format"],
        "header.point_data_record_format",
    )
    min_length = FORMAT_MIN_POINT_LENGTH[point_format]
    extra_lengths = {_extra_bytes_length(point_format, point) for point in points}
    if len(extra_lengths) > 1:
        raise ValueError("all points must use the same extra-bytes length")
    extra_length = extra_lengths.pop() if extra_lengths else 0
    point_record_length = min_length + extra_length

    canonical_vlrs: list[dict[str, Any]] = []
    vlr_payloads: list[bytes] = []
    for record in vlrs:
        canonical_record, payload = _canonical_record_payload(record, is_evlr=False)
        canonical_vlrs.append(canonical_record)
        vlr_payloads.append(payload)

    canonical_evlrs: list[dict[str, Any]] = []
    evlr_payloads: list[bytes] = []
    for record in evlrs:
        canonical_record, payload = _canonical_record_payload(record, is_evlr=True)
        canonical_evlrs.append(canonical_record)
        evlr_payloads.append(payload)

    point_bytes = [_point_bytes(point_format, point) for point in points]
    if any(len(value) != point_record_length for value in point_bytes):
        raise ValueError("point record length does not match point format plus extra bytes")

    offset_to_point_data = 375 + sum(54 + len(payload) for payload in vlr_payloads)
    point_data_size = sum(len(value) for value in point_bytes)
    first_evlr_offset = offset_to_point_data + point_data_size if canonical_evlrs else 0

    waveform_offset = 0
    if canonical_evlrs:
        running_offset = first_evlr_offset
        for record, payload in zip(canonical_evlrs, evlr_payloads, strict=True):
            if record["kind"] == "waveform_data_packets" and waveform_offset == 0:
                waveform_offset = running_offset
            running_offset += 60 + len(payload)

    legacy_mode = _maintains_legacy_compatibility(
        {"header": header, "points": points, "vlrs": canonical_vlrs, "evlrs": canonical_evlrs},
        len(points),
    )
    legacy_point_count = len(points) if legacy_mode else 0
    legacy_points_by_return = _counts_by_return(points, 5) if legacy_mode else [0, 0, 0, 0, 0]

    coordinates = [_point_actual_coordinates(point, header) for point in points]
    if coordinates:
        xs, ys, zs = zip(*coordinates, strict=True)
        min_x = min(xs)
        max_x = max(xs)
        min_y = min(ys)
        max_y = max(ys)
        min_z = min(zs)
        max_z = max(zs)
    else:
        min_x = max_x = min_y = max_y = min_z = max_z = 0.0

    header.update(
        {
            "header_size": 375,
            "offset_to_point_data": offset_to_point_data,
            "number_of_variable_length_records": len(canonical_vlrs),
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
            "number_of_extended_variable_length_records": len(canonical_evlrs),
            "number_of_point_records": len(points),
            "number_of_points_by_return": _counts_by_return(points, 15),
        }
    )

    return {
        "header": header,
        "vlrs": canonical_vlrs,
        "points": points,
        "evlrs": canonical_evlrs,
    }


def encode_dataset(dataset: dict[str, Any]) -> bytes:
    canonical = canonical_dataset(dataset)
    header = cast(dict[str, Any], canonical["header"])
    points = cast(list[dict[str, Any]], canonical["points"])
    vlrs = cast(list[dict[str, Any]], canonical["vlrs"])
    evlrs = cast(list[dict[str, Any]], canonical["evlrs"])

    point_format = _ensure_int(
        header["point_data_record_format"],
        "header.point_data_record_format",
    )
    point_bytes = [_point_bytes(point_format, point) for point in points]
    canonical_vlrs = [_canonical_record_payload(record, is_evlr=False) for record in vlrs]
    canonical_evlrs = [_canonical_record_payload(record, is_evlr=True) for record in evlrs]

    header_bytes = bytearray()
    header_bytes.extend(b"LASF")
    header_bytes.extend(
        struct.pack(
            "<HH",
            _ensure_int(header["file_source_id"], "header.file_source_id"),
            _ensure_int(header["global_encoding"], "header.global_encoding"),
        )
    )
    header_bytes.extend(
        _project_id_bytes(_ensure_string(header["project_id"], "header.project_id"))
    )
    header_bytes.extend(
        struct.pack(
            "<BB",
            _ensure_int(header["version_major"], "header.version_major"),
            _ensure_int(header["version_minor"], "header.version_minor"),
        )
    )
    header_bytes.extend(
        _encode_fixed_ascii(
            header["system_identifier"],
            32,
            "header.system_identifier",
        )
    )
    header_bytes.extend(
        _encode_fixed_ascii(header["generating_software"], 32, "header.generating_software")
    )
    header_bytes.extend(
        struct.pack(
            "<HHHLLBH",
            _ensure_int(header["file_creation_day_of_year"], "header.file_creation_day_of_year"),
            _ensure_int(header["file_creation_year"], "header.file_creation_year"),
            _ensure_int(header["header_size"], "header.header_size"),
            _ensure_int(header["offset_to_point_data"], "header.offset_to_point_data"),
            _ensure_int(
                header["number_of_variable_length_records"],
                "header.number_of_variable_length_records",
            ),
            point_format,
            _ensure_int(header["point_data_record_length"], "header.point_data_record_length"),
        )
    )
    header_bytes.extend(
        struct.pack(
            "<L5L",
            _ensure_int(
                header["legacy_number_of_point_records"],
                "header.legacy_number_of_point_records",
            ),
            *[
                _ensure_int(value, "legacy_number_of_points_by_return")
                for value in cast(list[Any], header["legacy_number_of_points_by_return"])
            ],
        )
    )
    header_bytes.extend(
        struct.pack(
            "<12d",
            _ensure_number(header["x_scale_factor"], "header.x_scale_factor"),
            _ensure_number(header["y_scale_factor"], "header.y_scale_factor"),
            _ensure_number(header["z_scale_factor"], "header.z_scale_factor"),
            _ensure_number(header["x_offset"], "header.x_offset"),
            _ensure_number(header["y_offset"], "header.y_offset"),
            _ensure_number(header["z_offset"], "header.z_offset"),
            _ensure_number(header["max_x"], "header.max_x"),
            _ensure_number(header["min_x"], "header.min_x"),
            _ensure_number(header["max_y"], "header.max_y"),
            _ensure_number(header["min_y"], "header.min_y"),
            _ensure_number(header["max_z"], "header.max_z"),
            _ensure_number(header["min_z"], "header.min_z"),
        )
    )
    header_bytes.extend(
        struct.pack(
            "<QQLQ15Q",
            _ensure_int(
                header["start_of_waveform_data_packet_record"],
                "header.start_of_waveform_data_packet_record",
            ),
            _ensure_int(
                header["start_of_first_extended_variable_length_record"],
                "header.start_of_first_extended_variable_length_record",
            ),
            _ensure_int(
                header["number_of_extended_variable_length_records"],
                "header.number_of_extended_variable_length_records",
            ),
            _ensure_int(header["number_of_point_records"], "header.number_of_point_records"),
            *[
                _ensure_int(value, "number_of_points_by_return")
                for value in cast(list[Any], header["number_of_points_by_return"])
            ],
        )
    )
    assert len(header_bytes) == 375

    blob = bytearray(header_bytes)
    for record, payload in canonical_vlrs:
        blob.extend(struct.pack("<H", 0))
        blob.extend(_encode_fixed_ascii(record["user_id"], 16, "record.user_id"))
        blob.extend(struct.pack("<H", _ensure_int(record["record_id"], "record.record_id")))
        blob.extend(struct.pack("<H", len(payload)))
        blob.extend(_encode_fixed_ascii(record["description"], 32, "record.description"))
        blob.extend(payload)
    for point_data in point_bytes:
        blob.extend(point_data)
    for record, payload in canonical_evlrs:
        blob.extend(struct.pack("<H", 0))
        blob.extend(_encode_fixed_ascii(record["user_id"], 16, "record.user_id"))
        blob.extend(struct.pack("<H", _ensure_int(record["record_id"], "record.record_id")))
        blob.extend(struct.pack("<Q", len(payload)))
        blob.extend(_encode_fixed_ascii(record["description"], 32, "record.description"))
        blob.extend(payload)
    return bytes(blob)


def encode_request_for_inspect(dataset: dict[str, Any]) -> dict[str, Any]:
    return {"action": "inspect", "las_b64": b64encode_bytes(encode_dataset(dataset))}


def encode_request_for_render(dataset: dict[str, Any]) -> dict[str, Any]:
    return {"action": "render", "dataset": clone(dataset)}


def payload_dataset(payload: dict[str, Any]) -> dict[str, Any]:
    return cast(dict[str, Any], cast(dict[str, Any], payload["result"])["dataset"])


def payload_las_bytes(payload: dict[str, Any]) -> bytes:
    return b64decode_text(cast(dict[str, Any], payload["result"])["las_b64"])
