from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
from gedcom_support import (
    document_text,
    individual_record_block,
    multimedia_record_block,
    node,
    sample_dataset,
    submitter_record_block,
)

from conftest import run_gedcom


def _has_error_code(payload: dict[str, object] | None, code: str) -> bool:
    if payload is None:
        return False
    error = payload.get("error")
    return isinstance(error, dict) and cast(dict[str, object], error).get("code") == code


def _assert_invalid_document(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    text: str,
) -> None:
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert _has_error_code(payload, "invalid_document")


@pytest.mark.parametrize(
    "date_payload",
    [
        "",
        "1900",
        "JAN 1900",
        "1 JAN 1900",
        "ABT 1 JAN 1900",
        "BET 1900 AND 1901",
        "FROM JULIAN 1670 TO GREGORIAN 1800",
    ],
)
def test_date_value_forms_are_accepted(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    date_payload: str,
) -> None:
    date_line = "2 DATE" if date_payload == "" else f"2 DATE {date_payload}"
    text = document_text(individual_record_block(extra_lines=["1 BIRT Y", date_line]))
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None


@pytest.mark.parametrize(
    "date_payload",
    ["1900/01", "BET 1900 1901", "1 FOO 1900", "GREGORIAN BCE", "FRENCH_R 1 VEND 1 BCE"],
)
def test_date_value_rejects_invalid_gedcom7_syntax(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    date_payload: str,
) -> None:
    _assert_invalid_document(
        submission_command,
        tmp_path,
        document_text(individual_record_block(extra_lines=["1 BIRT Y", f"2 DATE {date_payload}"])),
    )


def test_julian_bce_date_is_accepted(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    text = document_text(
        individual_record_block(extra_lines=["1 BIRT Y", "2 DATE JULIAN 1 JAN 1 BCE"])
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None


def test_change_date_requires_date_exact(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _assert_invalid_document(
        submission_command,
        tmp_path,
        document_text(submitter_record_block(extra_lines=["1 CHAN", "2 DATE 1900"])),
    )


@pytest.mark.parametrize("time_payload", ["2:50", "02:50", "23:59:59.123Z"])
def test_time_payload_forms_are_accepted(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    time_payload: str,
) -> None:
    text = document_text(
        submitter_record_block(
            extra_lines=["1 CHAN", "2 DATE 1 JAN 1900", f"3 TIME {time_payload}"]
        )
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None


@pytest.mark.parametrize("time_payload", ["24:00:00", "12:60", "12:30:60"])
def test_time_rejects_end_of_day_and_leap_second(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    time_payload: str,
) -> None:
    _assert_invalid_document(
        submission_command,
        tmp_path,
        document_text(
            submitter_record_block(
                extra_lines=["1 CHAN", "2 DATE 1 JAN 1900", f"3 TIME {time_payload}"]
            )
        ),
    )


@pytest.mark.parametrize("age_payload", ["32y", "< 8d", "> 1y 30m", "8w 30d"])
def test_age_duration_forms_are_accepted(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    age_payload: str,
) -> None:
    text = document_text(
        individual_record_block(xref="@I1@"),
        individual_record_block(xref="@I2@"),
        [
            "0 @F1@ FAM",
            "1 HUSB @I1@",
            "1 WIFE @I2@",
            "1 MARR",
            "2 HUSB",
            f"3 AGE {age_payload}",
        ],
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None


def test_age_rejects_legacy_phrase_payload(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _assert_invalid_document(
        submission_command,
        tmp_path,
        document_text(
            individual_record_block(xref="@I1@"),
            individual_record_block(xref="@I2@"),
            [
                "0 @F1@ FAM",
                "1 HUSB @I1@",
                "1 WIFE @I2@",
                "1 MARR",
                "2 HUSB",
                "3 AGE INFANT",
            ],
        ),
    )


def test_language_payloads_are_validated(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    _assert_invalid_document(
        submission_command,
        tmp_path,
        document_text(submitter_record_block(extra_lines=["1 LANG en_US"])),
    )


def test_invalid_email_payload_is_preserved(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    result, payload = run_gedcom(
        submission_command,
        {
            "action": "inspect",
            "gedcom_text": document_text(
                submitter_record_block(extra_lines=["1 EMAIL not-an-email"])
            ),
        },
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None


@pytest.mark.parametrize(
    "file_lines",
    [
        ["1 FILE /absolute/path.jpg", "2 FORM image/jpeg"],
        ["1 FILE media/../photo.jpg", "2 FORM image/jpeg"],
        ["1 FILE media\\photo.jpg", "2 FORM image/jpeg"],
        ["1 FILE media/photo.jpg?download=1", "2 FORM image/jpeg"],
        ["1 FILE media/photo.jpg", "2 FORM image"],
    ],
)
def test_file_path_and_media_type_payloads_are_validated(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    file_lines: list[str],
) -> None:
    _assert_invalid_document(
        submission_command,
        tmp_path,
        document_text(multimedia_record_block(include_file=False, extra_lines=file_lines)),
    )


def test_percent_encoded_local_file_path_is_accepted(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    text = document_text(
        multimedia_record_block(
            include_file=False,
            extra_lines=["1 FILE media/John%20Doe.jpg", "2 FORM image/jpeg"],
        )
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None


@pytest.mark.parametrize(
    "map_lines",
    [
        ["4 LATI X42.36", "4 LONG W71.05"],
        ["4 LATI N90.1", "4 LONG W71.05"],
        ["4 LATI N42.36", "4 LONG W180.1"],
    ],
)
def test_latitude_and_longitude_payloads_are_validated(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    map_lines: list[str],
) -> None:
    _assert_invalid_document(
        submission_command,
        tmp_path,
        document_text(
            individual_record_block(
                extra_lines=[
                    "1 BIRT Y",
                    "2 PLAC Boston",
                    "3 MAP",
                    *map_lines,
                ]
            )
        ),
    )


@pytest.mark.parametrize(
    "extra_lines",
    [
        ["1 SEX Z"],
        ["1 RESN SECRET"],
        ["1 FAMC @F1@", "2 PEDI UNKNOWN"],
        ["1 NAME John /Doe/", "2 TYPE NICKNAME"],
        ["1 ASSO @I2@", "2 ROLE witness"],
    ],
)
def test_enum_payloads_are_validated(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    extra_lines: list[str],
) -> None:
    _assert_invalid_document(
        submission_command,
        tmp_path,
        document_text(
            individual_record_block(extra_lines=extra_lines),
            individual_record_block(xref="@I2@"),
            ["0 @F1@ FAM"],
        ),
    )


@pytest.mark.parametrize(
    "extra_lines",
    [
        ["1 SEX _LOCAL_SEX"],
        ["1 RESN CONFIDENTIAL, _LOCAL_RESTRICTION"],
        ["1 FAMC @F1@", "2 PEDI _LOCAL_PEDIGREE"],
        ["1 NAME John /Doe/", "2 TYPE _LOCAL_NAME_TYPE"],
        ["1 ASSO @I2@", "2 ROLE _LOCAL_ROLE"],
    ],
)
def test_extension_enum_payloads_are_accepted(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    extra_lines: list[str],
) -> None:
    text = document_text(
        individual_record_block(extra_lines=extra_lines),
        individual_record_block(xref="@I2@"),
        ["0 @F1@ FAM"],
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None


def test_render_rejects_invalid_datatype_payloads(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    dataset = sample_dataset()
    dataset["records"][3]["children"][1] = node("SEX", "Z")
    result, payload = run_gedcom(
        submission_command,
        {"action": "render", "dataset": dataset},
        tmp_path,
    )
    assert result.returncode == 1
    assert _has_error_code(payload, "invalid_request")
