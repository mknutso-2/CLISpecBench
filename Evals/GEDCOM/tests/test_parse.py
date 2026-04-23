from __future__ import annotations

from pathlib import Path

import pytest
from gedcom_support import (
    official_record_fragments,
    sample_dataset,
    sample_gedcom_text,
    wrap_record_fragment,
)

from conftest import run_gedcom


def test_parses_sample_dataset_to_generic_tree(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": sample_gedcom_text()},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    assert payload["result"]["dataset"] == sample_dataset()


def test_roundtrip_preserves_sample_dataset_tree(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    dataset = sample_dataset()
    render_result, render_payload = run_gedcom(
        submission_command,
        {"action": "render", "dataset": dataset},
        tmp_path,
    )
    assert render_result.returncode == 0
    assert render_payload is not None

    inspect_result, inspect_payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": render_payload["result"]["gedcom_text"]},
        tmp_path,
    )
    assert inspect_result.returncode == 0
    assert inspect_payload is not None
    assert inspect_payload["result"]["dataset"] == dataset


def test_render_preserves_multiline_and_escaped_payload_content(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_gedcom(
        submission_command,
        {"action": "render", "dataset": sample_dataset()},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    text = payload["result"]["gedcom_text"]
    assert "1 NOTE Lead genealogist" in text
    assert "2 CONT Chicago office" in text
    assert "1 NOTE Household record" in text
    assert "2 CONT for downtown apartment" in text
    assert "1 NOTE @@handle" in text


@pytest.mark.parametrize(
    ("label", "fragment_text"),
    official_record_fragments(),
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_official_record_fragments_parse_when_wrapped_as_dataset(
    label: str,
    fragment_text: str,
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    del label
    dataset_text = wrap_record_fragment(fragment_text)
    inspect_result, inspect_payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": dataset_text},
        tmp_path,
    )
    assert inspect_result.returncode == 0
    assert inspect_payload is not None

    render_result, render_payload = run_gedcom(
        submission_command,
        {"action": "render", "dataset": inspect_payload["result"]["dataset"]},
        tmp_path,
    )
    assert render_result.returncode == 0
    assert render_payload is not None
    assert render_payload["result"]["gedcom_text"] == dataset_text
