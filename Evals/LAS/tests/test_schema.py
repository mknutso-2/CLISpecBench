from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from .conftest import run_las
from .las_support import (
    b64decode_text,
    dataset_for_point_format,
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
