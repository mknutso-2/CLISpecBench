from __future__ import annotations

from pathlib import Path

from gedcom_support import sample_dataset, sample_gedcom_text

from conftest import run_gedcom


def test_inspect_success_schema(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
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


def test_render_success_schema(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
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


def test_error_schema_for_invalid_document(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": "0 TRLR\n"},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "invalid_document"
    assert payload["result"] is None
