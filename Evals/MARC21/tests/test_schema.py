from __future__ import annotations

from pathlib import Path

from marc21_support import sample_marcxml, sample_record

from conftest import run_marc21


def test_inspect_success_schema(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    render_result, render_payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": sample_record()},
        tmp_path,
    )
    assert render_result.returncode == 0
    assert render_payload is not None
    inspect_result, inspect_payload = run_marc21(
        submission_command,
        {"action": "inspect", "record_b64": render_payload["result"]["record_b64"]},
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


def test_render_iso2709_success_schema(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "render_iso2709", "record": sample_record()},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    assert isinstance(payload["result"]["record_b64"], str)


def test_render_marcxml_success_schema(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_marc21(
        submission_command,
        {"action": "render_marcxml", "record": sample_record()},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
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
