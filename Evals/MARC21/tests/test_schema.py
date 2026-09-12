from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from conftest import b64, run_marc21
from marc21_support import encode_iso2709_record, sample_marcxml, sample_record


def test_inspect_success_schema(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    inspect_result, inspect_payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": b64(encode_iso2709_record(sample_record()))},
        tmp_path,
    )
    assert inspect_result.returncode == 0
    assert inspect_payload is not None
    assert inspect_payload["status"] == "ok"
    assert inspect_payload["error"] is None
    assert isinstance(inspect_payload["result"]["record"]["control_fields"], list)


def test_inspect_marcxml_success_schema(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "inspect_marcxml", "marcxml": sample_marcxml()},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    assert payload["status"] == "ok"
    assert payload["error"] is None
    assert isinstance(payload["result"]["record"]["data_fields"], list)


def test_render_iso2709_success_schema(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": sample_record()},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    assert payload["status"] == "ok"
    assert payload["error"] is None
    assert isinstance(payload["result"]["record_b64"], str)


def test_render_marcxml_success_schema(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "render_marcxml", "record": sample_record()},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    assert payload["status"] == "ok"
    assert payload["error"] is None
    assert isinstance(payload["result"]["marcxml"], str)


def test_error_schema_for_invalid_request(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "explode"},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "invalid_request"
    assert isinstance(payload["error"]["message"], str)
    assert payload["error"]["message"].strip()
    assert payload["result"] is None


@pytest.mark.parametrize(
    "action", ["inspect", "inspect_marcxml", "render_iso2709", "render_marcxml"]
)
def test_record_error_schema_per_action(
    action: str, submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # One unambiguous invalid leader isolates each interface's error mapping.
    # Domain cases observe rejection without repeating this envelope check.
    record = sample_record()
    record["leader_template"] = "X" + record["leader_template"][1:]
    request: dict[str, Any] = {"action": action}
    if action == "inspect":
        raw = bytearray(encode_iso2709_record(sample_record()))
        raw[0] = ord("X")
        request["record_b64"] = b64(bytes(raw))
    elif action == "inspect_marcxml":
        request["marcxml"] = sample_marcxml(record)
    else:
        # Leader/10 must be 2; a malformed normalization field could be
        # overwritten by a renderer before it reaches domain validation.
        record["leader_template"] = "00000nam a1200000 a 4500"
        request["record"] = record
    result, payload = run_marc21(submission_command, request, tmp_path)
    assert result.returncode == 1
    assert payload is not None
    assert payload["status"] == "error"
    expected_code = "invalid_record" if action.startswith("inspect") else "invalid_request"
    assert payload["error"]["code"] == expected_code
    assert isinstance(payload["error"]["message"], str)
    assert payload["error"]["message"].strip()
    assert payload["result"] is None


@pytest.mark.parametrize("action", ["inspect", "inspect_marcxml"])
def test_inspect_normalizes_serialized_leader(
    action: str, submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    record = sample_record()
    raw = encode_iso2709_record(record)
    request: dict[str, Any] = {"action": action}
    if action == "inspect":
        request["record_b64"] = b64(raw)
    else:
        # The source XML leader can carry concrete ISO 2709 transport digits.
        record["leader_template"] = raw[:24].decode("ascii")
        request["marcxml"] = sample_marcxml(record)
    _, payload = run_marc21(submission_command, request, tmp_path)
    assert payload is not None
    assert payload["result"]["record"]["leader_template"] == sample_record()["leader_template"]
