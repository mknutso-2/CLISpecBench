from __future__ import annotations

from pathlib import Path

from gedcom_support import sample_dataset, sample_gedcom_text

from conftest import run_gedcom


def test_missing_head_is_invalid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": "0 TRLR\n"},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_missing_trailer_is_invalid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = sample_gedcom_text().replace("0 TRLR\n", "")
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_head_requires_gedc_and_vers(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = sample_gedcom_text().replace("1 GEDC\n2 VERS 7.0\n", "")
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_second_head_record_is_invalid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    extra_head = "\n".join(["0 HEAD", "1 GEDC", "2 VERS 7.0"])
    text = sample_gedcom_text().replace("0 @U1@ SUBM", f"{extra_head}\n0 @U1@ SUBM", 1)
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_second_trailer_record_is_invalid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = sample_gedcom_text().replace("0 TRLR\n", "0 TRLR\n0 TRLR\n")
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_conc_is_invalid_in_gedcom7(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = sample_gedcom_text().replace(
        "1 NOTE Household record\n2 CONT for downtown apartment",
        "1 NOTE Household record\n2 CONC for downtown apartment",
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_trailer_may_not_have_children(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = sample_gedcom_text().replace("0 TRLR\n", "0 TRLR\n1 NOTE nope\n")
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_multiple_spaces_between_components_are_invalid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = sample_gedcom_text().replace("1 SOUR CLISpecBench", "1  SOUR CLISpecBench")
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_duplicate_xref_is_invalid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = sample_gedcom_text().replace("0 @N1@ SNOTE", "0 @U1@ SNOTE")
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_dangling_pointer_is_invalid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = sample_gedcom_text().replace("1 FAMS @F1@", "1 FAMS @F9@", 1)
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_void_pointer_is_allowed(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = sample_gedcom_text().replace("1 WIFE @I2@", "1 WIFE @VOID@")
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None


def test_unescaped_leading_at_in_non_pointer_payload_is_invalid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = sample_gedcom_text().replace("1 NOTE @@handle", "1 NOTE @handle@")
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_illegal_level_jump_is_invalid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = sample_gedcom_text().replace("1 NAME John /Doe/", "3 NAME John /Doe/")
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_banned_control_character_is_invalid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = sample_gedcom_text().replace("Example Researcher", "Example\u0001Researcher")
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_invalid_line_syntax_is_invalid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = sample_gedcom_text().replace("1 GEDC", "1")
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_render_rejects_non_list_records(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_gedcom(
        submission_command,
        {"action": "render", "dataset": {"records": {"tag": "HEAD"}}},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_node_with_non_string_tag(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    result, payload = run_gedcom(
        submission_command,
        {
            "action": "render",
            "dataset": {
                "records": [
                    {
                        "tag": 7,
                        "xref": None,
                        "payload": None,
                        "children": [],
                    },
                    *sample_dataset()["records"][1:],
                ]
            },
        },
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_duplicate_xref_in_dataset(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    dataset = sample_dataset()
    dataset["records"][2]["xref"] = "@U1@"
    result, payload = run_gedcom(
        submission_command,
        {"action": "render", "dataset": dataset},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_escapes_leading_at_in_non_pointer_payload(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    dataset = sample_dataset()
    dataset["records"][1]["children"][2]["payload"] = "@handle@"
    result, payload = run_gedcom(
        submission_command,
        {"action": "render", "dataset": dataset},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None
    assert "1 NOTE @@handle@" in payload["result"]["gedcom_text"]


def test_render_rejects_explicit_conc_node(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    dataset = sample_dataset()
    dataset["records"][1]["children"].append(
        {
            "tag": "CONC",
            "xref": None,
            "payload": "bad",
            "children": [],
        }
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "render", "dataset": dataset},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_banned_control_character(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    dataset = sample_dataset()
    dataset["records"][1]["children"][0]["payload"] = "Bad\u0001Name"
    result, payload = run_gedcom(
        submission_command,
        {"action": "render", "dataset": dataset},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"
