from __future__ import annotations

import base64
import io
import zipfile
from pathlib import Path
from typing import cast

from gedcom_support import (
    gedzip_b64,
    multimedia_record_block,
    node,
    read_gedzip_b64,
    sample_dataset,
    sample_gedcom_text,
)

from conftest import run_gedcom


def _has_error_code(payload: dict[str, object] | None, code: str) -> bool:
    if payload is None:
        return False
    error = payload.get("error")
    return isinstance(error, dict) and cast(dict[str, object], error).get("code") == code


def test_inspect_gedzip_returns_dataset_and_attachments(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    archive_b64 = gedzip_b64(
        sample_gedcom_text(),
        {"media/photo.jpg": b"jpeg bytes"},
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect_gedzip", "gedzip_b64": archive_b64},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    result_payload = cast(dict[str, object], payload.get("result"))
    assert result_payload["dataset"] == sample_dataset()
    assert result_payload["attachments"] == {
        "media/photo.jpg": base64.b64encode(b"jpeg bytes").decode("ascii")
    }


def test_render_gedzip_writes_dataset_and_attachments(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    attachment_b64 = base64.b64encode(b"jpeg bytes").decode("ascii")
    result, payload = run_gedcom(
        submission_command,
        {
            "action": "render_gedzip",
            "dataset": sample_dataset(),
            "attachments": {"media/photo.jpg": attachment_b64},
        },
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    result_payload = cast(dict[str, str], payload.get("result"))
    entries = read_gedzip_b64(result_payload["gedzip_b64"])
    assert entries["gedcom.ged"].decode("utf-8") == sample_gedcom_text()
    assert entries["media/photo.jpg"] == b"jpeg bytes"


def test_gedzip_requires_gedcom_dataset_entry(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("media/photo.jpg", b"jpeg bytes")
    result, payload = run_gedcom(
        submission_command,
        {
            "action": "inspect_gedzip",
            "gedzip_b64": base64.b64encode(buffer.getvalue()).decode("ascii"),
        },
        tmp_path,
    )
    assert result.returncode == 1
    assert _has_error_code(payload, "invalid_document")


def test_gedzip_requires_local_file_entries(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    text = "\n".join(
        [
            "0 HEAD",
            "1 GEDC",
            "2 VERS 7.0",
            "0 @O1@ OBJE",
            "1 FILE media/photo.jpg",
            "2 FORM image/jpeg",
            "0 TRLR",
            "",
        ]
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect_gedzip", "gedzip_b64": gedzip_b64(text)},
        tmp_path,
    )
    assert result.returncode == 1
    assert _has_error_code(payload, "invalid_document")


def test_gedzip_rejects_local_file_url_payloads(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    text = "\n".join(
        [
            "0 HEAD",
            "1 GEDC",
            "2 VERS 7.0",
            "0 @O1@ OBJE",
            "1 FILE file:///C:/Users/Matthew/photo.jpg",
            "2 FORM image/jpeg",
            "0 TRLR",
            "",
        ]
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect_gedzip", "gedzip_b64": gedzip_b64(text)},
        tmp_path,
    )
    assert result.returncode == 1
    assert _has_error_code(payload, "invalid_document")


def test_data_stream_allows_file_url_payloads_outside_gedzip(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    text = "\n".join(
        [
            "0 HEAD",
            "1 GEDC",
            "2 VERS 7.0",
            "0 @O1@ OBJE",
            "1 FILE file:///C:/Users/Matthew/photo.jpg",
            "2 FORM image/jpeg",
            "0 TRLR",
            "",
        ]
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None


def test_gedzip_matches_percent_encoded_file_payload_to_unescaped_entry_name(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    text = "\n".join(
        [
            "0 HEAD",
            "1 GEDC",
            "2 VERS 7.0",
            "0 @O1@ OBJE",
            "1 FILE media/John%20Doe.jpg",
            "2 FORM image/jpeg",
            "0 TRLR",
            "",
        ]
    )
    result, payload = run_gedcom(
        submission_command,
        {
            "action": "inspect_gedzip",
            "gedzip_b64": gedzip_b64(text, {"media/John Doe.jpg": b"jpeg bytes"}),
        },
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None


def test_render_gedzip_rejects_missing_required_attachment(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    dataset = {
        "records": [
            sample_dataset()["records"][0],
            node(
                "OBJE",
                xref="@O1@",
                children=[
                    node(
                        "FILE",
                        "media/photo.jpg",
                        children=[node("FORM", "image/jpeg")],
                    )
                ],
            ),
            sample_dataset()["records"][-1],
        ],
    }
    result, payload = run_gedcom(
        submission_command,
        {"action": "render_gedzip", "dataset": dataset, "attachments": {}},
        tmp_path,
    )
    assert result.returncode == 1
    assert _has_error_code(payload, "invalid_request")


def test_gedzip_rejects_reserved_dataset_entry_as_local_file(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    text = "\n".join(
        [
            "0 HEAD",
            "1 GEDC",
            "2 VERS 7.0",
            *multimedia_record_block(
                include_file=False,
                extra_lines=["1 FILE gedcom.ged", "2 FORM text/plain"],
            ),
            "0 TRLR",
            "",
        ]
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect_gedzip", "gedzip_b64": gedzip_b64(text)},
        tmp_path,
    )
    assert result.returncode == 1
    assert _has_error_code(payload, "invalid_document")
