from __future__ import annotations

import base64
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from .conftest import run_las
from .las_support import (
    b64decode_text,
    dataset_for_point_format,
    encode_dataset,
    encode_request_for_inspect,
    encode_request_for_render,
)


def test_inspect_response_schema(submission_command: Sequence[str], tmp_path: Path) -> None:
    result, payload = run_las(
        submission_command,
        encode_request_for_inspect(dataset_for_point_format(0)),
        tmp_path,
    )

    assert result.returncode == 0
    assert payload is not None
    assert payload == {
        "status": "ok",
        "error": None,
        "result": payload["result"],
    }
    assert "dataset" in cast(dict[str, Any], payload["result"])


def test_render_response_schema(submission_command: Sequence[str], tmp_path: Path) -> None:
    result, payload = run_las(
        submission_command,
        encode_request_for_render(dataset_for_point_format(6)),
        tmp_path,
    )

    assert result.returncode == 0
    assert payload is not None
    assert payload == {
        "status": "ok",
        "error": None,
        "result": payload["result"],
    }
    assert "las_b64" in cast(dict[str, Any], payload["result"])
    b64decode_text(cast(dict[str, Any], payload["result"])["las_b64"])


def test_invalid_action_uses_invalid_request_code(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    result, payload = run_las(submission_command, {"action": "explode"}, tmp_path)

    assert result.returncode == 1
    assert payload is not None
    assert payload["status"] == "error"
    assert cast(dict[str, Any], payload["error"])["code"] == "invalid_request"


def test_non_object_request_is_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    request_file = tmp_path / "request.json"
    output_file = tmp_path / "response.json"
    request_file.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    result = subprocess.run(
        [*submission_command, "--input", str(request_file), "--output", str(output_file)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    payload = cast(dict[str, Any], json.loads(output_file.read_text(encoding="utf-8")))

    assert result.returncode == 1
    assert payload["status"] == "error"
    assert cast(dict[str, Any], payload["error"])["code"] == "invalid_request"


def test_inspect_error_envelope_shape(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    """Gate: malformed inspect input produces the documented error envelope."""

    broken = bytearray(encode_dataset(dataset_for_point_format(0)))
    broken[0:4] = b"BAD!"
    request = {"action": "inspect", "las_b64": base64.b64encode(bytes(broken)).decode("ascii")}
    result, payload = run_las(submission_command, request, tmp_path)

    assert result.returncode == 1
    assert payload is not None
    assert payload["status"] == "error"
    assert payload["result"] is None
    error = cast(dict[str, Any], payload["error"])
    assert isinstance(error.get("code"), str)
    assert isinstance(error.get("message"), str)
    assert error["code"] == "invalid_document"


def test_render_error_envelope_shape(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    """Gate: malformed render input produces the documented error envelope."""

    dataset = dataset_for_point_format(0)
    dataset["header"]["project_id"] = "not-a-uuid"
    result, payload = run_las(submission_command, encode_request_for_render(dataset), tmp_path)

    assert result.returncode == 1
    assert payload is not None
    assert payload["status"] == "error"
    assert payload["result"] is None
    error = cast(dict[str, Any], payload["error"])
    assert isinstance(error.get("code"), str)
    assert isinstance(error.get("message"), str)
    assert error["code"] == "invalid_request"


def test_inspect_malformed_las_b64_routes_to_invalid_request(
    submission_command: Sequence[str],
    tmp_path: Path,
) -> None:
    """Routing: malformed base64 is a request-level error, not a document error.

    Pinning this distinction in one place keeps validation tests in
    `test_validation.py` focused on whether the input was rejected at all,
    rather than each test asserting the same `invalid_request` /
    `invalid_document` routing rule.
    """

    result, payload = run_las(
        submission_command,
        {"action": "inspect", "las_b64": "!!!!"},
        tmp_path,
    )

    assert result.returncode == 1
    assert payload is not None
    error = cast(dict[str, Any], payload["error"])
    assert error["code"] == "invalid_request"
