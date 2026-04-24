from __future__ import annotations

from pathlib import Path
from typing import cast

from gedcom_spec_support import record_root_specs, y_or_null_event_cases
from gedcom_support import (
    clone_dataset,
    document_text,
    individual_record_block,
    multimedia_record_block,
    node,
    repository_record_block,
    sample_dataset,
    sample_gedcom_text,
    shared_note_record_block,
    submitter_record_block,
)

from conftest import run_gedcom

_RECORD_ROOT_SPECS = record_root_specs()
_XREF_REQUIRED_RECORD_TAGS = sorted(
    entry.tag for entry in _RECORD_ROOT_SPECS if entry.xref_token is not None
)
_Y_OR_NULL_EVENT_CASES = y_or_null_event_cases()


def _unexpected_result(
    returncode: int, payload: dict[str, object] | None, expected_code: str
) -> bool:
    if returncode != 1 or payload is None:
        return True
    error = payload.get("error")
    if not isinstance(error, dict):
        return True
    error_dict = cast(dict[str, object], error)
    return error_dict.get("code") != expected_code


def test_missing_head_is_invalid(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": "0 TRLR\n"},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_missing_trailer_is_invalid(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = sample_gedcom_text().replace("0 TRLR\n", "")
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_head_requires_gedc_and_vers(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = sample_gedcom_text().replace("1 GEDC\n2 VERS 7.0\n", "")
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_second_head_record_is_invalid(submission_command: tuple[str, ...], tmp_path: Path) -> None:
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


def test_conc_is_invalid_in_gedcom7(submission_command: tuple[str, ...], tmp_path: Path) -> None:
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


def test_trailer_may_not_have_children(submission_command: tuple[str, ...], tmp_path: Path) -> None:
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


def test_duplicate_xref_is_invalid(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = sample_gedcom_text().replace("0 @N1@ SNOTE", "0 @U1@ SNOTE")
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_dangling_pointer_is_invalid(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = sample_gedcom_text().replace("1 FAMS @F1@", "1 FAMS @F9@", 1)
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_void_pointer_is_allowed(submission_command: tuple[str, ...], tmp_path: Path) -> None:
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


def test_illegal_level_jump_is_invalid(submission_command: tuple[str, ...], tmp_path: Path) -> None:
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


def test_unknown_top_level_record_tag_is_invalid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = document_text(["0 @X1@ FOO"])
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_top_level_record_types_from_official_grammar_require_xref(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    block_by_tag = {
        "FAM": ["0 FAM"],
        "INDI": ["0 INDI"],
        "OBJE": ["0 OBJE", "1 FILE photo.jpg", "2 FORM image/jpeg"],
        "REPO": ["0 REPO", "1 NAME Example Repository"],
        "SNOTE": ["0 SNOTE Shared note"],
        "SOUR": ["0 SOUR", "1 TITL Example Source"],
        "SUBM": ["0 SUBM", "1 NAME Example Submitter"],
    }
    failures: list[str] = []
    for tag in _XREF_REQUIRED_RECORD_TAGS:
        result, payload = run_gedcom(
            submission_command,
            {"action": "inspect", "gedcom_text": document_text(block_by_tag[tag])},
            tmp_path,
        )
        if _unexpected_result(result.returncode, payload, "invalid_document"):
            failures.append(tag)
    assert not failures, f"Top-level xref requirement failures: {', '.join(failures)}"


def test_official_y_or_null_event_tags_reject_other_payloads(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    failures: list[str] = []
    for record_tag, event_tag in _Y_OR_NULL_EVENT_CASES:
        text = document_text(
            [
                f"0 @{record_tag}1@ {record_tag}",
                f"1 {event_tag} N",
            ]
        )
        result, payload = run_gedcom(
            submission_command,
            {"action": "inspect", "gedcom_text": text},
            tmp_path,
        )
        if _unexpected_result(result.returncode, payload, "invalid_document"):
            failures.append(f"{record_tag}:{event_tag}")
    assert not failures, f"Y-or-null payload failures: {', '.join(failures)}"


def test_head_payload_is_invalid(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = sample_gedcom_text().replace("0 HEAD", "0 HEAD nope", 1)
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_shared_note_record_requires_payload(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = document_text(shared_note_record_block(payload=None))
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_header_place_requires_form(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = document_text(
        submitter_record_block(),
        head_lines=[
            "0 HEAD",
            "1 GEDC",
            "2 VERS 7.0",
            "1 SUBM @U1@",
            "1 PLAC",
        ],
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_header_place_may_not_have_payload(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = document_text(
        submitter_record_block(),
        head_lines=[
            "0 HEAD",
            "1 GEDC",
            "2 VERS 7.0",
            "1 SUBM @U1@",
            "1 PLAC Custom payload",
            "2 FORM City, State",
        ],
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_submitter_requires_name(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = document_text(submitter_record_block(include_name=False))
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_repository_requires_name(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = document_text(repository_record_block(include_name=False))
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_multimedia_record_requires_file(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = document_text(multimedia_record_block(include_file=False))
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_file_requires_form(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = document_text(multimedia_record_block(include_form=False))
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_file_tran_requires_form(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = document_text(multimedia_record_block(extra_lines=["2 TRAN thumb.jpg"]))
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_change_date_requires_date(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = document_text(submitter_record_block(extra_lines=["1 CHAN"]))
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_creation_date_requires_date(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = document_text(submitter_record_block(extra_lines=["1 CREA"]))
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_association_requires_role(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = document_text(individual_record_block(extra_lines=["1 ASSO @I2@"]), ["0 @I2@ INDI"])
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_place_map_requires_lati(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = document_text(
        individual_record_block(
            extra_lines=[
                "1 BIRT Y",
                "2 PLAC Boston, Massachusetts",
                "3 MAP",
                "4 LONG W71.05",
            ]
        )
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_place_map_requires_long(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = document_text(
        individual_record_block(
            extra_lines=[
                "1 BIRT Y",
                "2 PLAC Boston, Massachusetts",
                "3 MAP",
                "4 LATI N42.36",
            ]
        )
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_name_translation_requires_lang(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = document_text(
        individual_record_block(
            extra_lines=[
                "1 NAME John /Doe/",
                "2 TRAN Jean /Doe/",
            ]
        )
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_individual_even_tag_requires_type(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = document_text(individual_record_block(extra_lines=["1 EVEN Reunion"]))
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_family_event_husb_requires_age(
    submission_command: tuple[str, ...], tmp_path: Path
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
        ],
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_child_link_is_only_valid_under_family_records(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = document_text(
        individual_record_block(extra_lines=["1 CHIL @I2@"]),
        individual_record_block(xref="@I2@"),
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_individual_fact_requires_type(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    text = document_text(individual_record_block(extra_lines=["1 FACT Veteran"]))
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_place_translation_requires_lang(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = document_text(
        individual_record_block(
            extra_lines=[
                "1 BIRT Y",
                "2 PLAC Boston, Massachusetts",
                "3 TRAN Boston, Mass.",
            ]
        )
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_document"


def test_adoption_famc_substructure_allows_enum_payload(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    text = document_text(
        individual_record_block(
            extra_lines=[
                "1 ADOP Y",
                "2 FAMC @F1@",
                "3 ADOP HUSB",
            ]
        ),
        ["0 @F1@ FAM"],
    )
    result, payload = run_gedcom(
        submission_command,
        {"action": "inspect", "gedcom_text": text},
        tmp_path,
    )
    assert result.returncode == 0
    assert payload is not None


def test_inspect_rejects_pointer_to_wrong_record_type(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    cases = [
        ("FAMS", "@N1@", shared_note_record_block(xref="@N1@", payload="Shared note")),
        ("SUBM", "@I2@", individual_record_block(xref="@I2@")),
        ("SNOTE", "@I2@", individual_record_block(xref="@I2@")),
        ("OBJE", "@I2@", individual_record_block(xref="@I2@")),
        ("SOUR", "@I2@", individual_record_block(xref="@I2@")),
    ]
    failures: list[str] = []
    for tag, reference, target_block in cases:
        text = document_text(
            individual_record_block(extra_lines=[f"1 {tag} {reference}"]),
            target_block,
        )
        result, payload = run_gedcom(
            submission_command,
            {"action": "inspect", "gedcom_text": text},
            tmp_path,
        )
        if _unexpected_result(result.returncode, payload, "invalid_document"):
            failures.append(tag)
    assert not failures, f"Inspect pointer target failures: {', '.join(failures)}"


def test_render_rejects_pointer_to_wrong_record_type(
    submission_command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    failures: list[str] = []
    for tag, reference in [
        ("FAMS", "@N1@"),
        ("SUBM", "@I1@"),
        ("SNOTE", "@I1@"),
        ("OBJE", "@I1@"),
        ("SOUR", "@I1@"),
    ]:
        dataset = clone_dataset(sample_dataset())
        dataset["records"][3]["children"].append(node(tag, reference))
        result, payload = run_gedcom(
            submission_command,
            {"action": "render", "dataset": dataset},
            tmp_path,
        )
        if _unexpected_result(result.returncode, payload, "invalid_request"):
            failures.append(tag)
    assert not failures, f"Render pointer target failures: {', '.join(failures)}"


def test_render_rejects_name_translation_without_lang(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    dataset = clone_dataset(sample_dataset())
    dataset["records"][3]["children"][0]["children"].append(node("TRAN", "Jean /Doe/"))
    result, payload = run_gedcom(
        submission_command,
        {"action": "render", "dataset": dataset},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_multimedia_record_without_file_form(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    dataset = {
        "records": [
            node("HEAD", children=[node("GEDC", children=[node("VERS", "7.0")])]),
            node("OBJE", xref="@O1@", children=[node("FILE", "photo.jpg")]),
            node("TRLR"),
        ]
    }
    result, payload = run_gedcom(
        submission_command,
        {"action": "render", "dataset": dataset},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_multimedia_record_with_top_level_titl(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    dataset = {
        "records": [
            node("HEAD", children=[node("GEDC", children=[node("VERS", "7.0")])]),
            node(
                "OBJE",
                xref="@O1@",
                children=[
                    node("FILE", "photo.jpg", children=[node("FORM", "image/jpeg")]),
                    node("TITL", "Wrong level"),
                ],
            ),
            node("TRLR"),
        ]
    }
    result, payload = run_gedcom(
        submission_command,
        {"action": "render", "dataset": dataset},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"


def test_render_rejects_submitter_without_name(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    dataset = {
        "records": [
            node("HEAD", children=[node("GEDC", children=[node("VERS", "7.0")])]),
            node("SUBM", xref="@U1@", children=[]),
            node("TRLR"),
        ]
    }
    result, payload = run_gedcom(
        submission_command,
        {"action": "render", "dataset": dataset},
        tmp_path,
    )
    assert result.returncode == 1
    assert payload is not None
    assert payload["error"]["code"] == "invalid_request"
