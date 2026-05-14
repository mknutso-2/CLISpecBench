from __future__ import annotations

from pathlib import Path

from conftest import run_gedcom
from gedcom_support import sample_dataset, sample_gedcom_text


def test_inspect_success_schema(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": sample_gedcom_text()},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    assert payload["status"] == "ok"
    assert payload["error"] is None
    dataset = payload["result"]["dataset"]
    assert isinstance(dataset["records"], list)
    head = dataset["records"][0]
    assert set(head) == {"tag", "xref", "payload", "children"}
    assert isinstance(head["children"], list)


def test_render_success_schema(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    result, payload = run_gedcom(
        submission_command,
        {"action": "render", "dataset": sample_dataset()},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    assert payload["status"] == "ok"
    assert payload["error"] is None
    assert isinstance(payload["result"]["gedcom_text"], str)


def test_error_response_schema_for_invalid_request(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_gedcom(
        submission_command,
        {"action": "not_a_real_action"},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "invalid_request"
    assert isinstance(payload["error"]["message"], str)
    assert payload["result"] is None
