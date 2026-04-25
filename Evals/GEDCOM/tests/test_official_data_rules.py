from __future__ import annotations

import json
from pathlib import Path
from typing import cast

_DATA_RULES_PATH = Path(__file__).resolve().parent / "generated" / "gedcom_data_rules.json"


def _data_rules() -> dict[str, object]:
    return cast(dict[str, object], json.loads(_DATA_RULES_PATH.read_text(encoding="utf-8")))


def test_generated_data_rules_cover_all_official_enum_sets() -> None:
    rules = _data_rules()
    enumerations = cast(dict[str, list[str]], rules["enumerations"])
    assert set(enumerations) >= {
        "ADOP",
        "EVEN",
        "EVENATTR",
        "MEDI",
        "PEDI",
        "QUAY",
        "RESN",
        "ROLE",
        "SEX",
        "FAMC-STAT",
        "ord-STAT",
        "NAME-TYPE",
    }
    assert enumerations["SEX"] == ["M", "F", "X", "U"]
    assert "PHOTO" in enumerations["MEDI"]
    assert "WITN" in enumerations["ROLE"]


def test_generated_data_rules_record_datatype_and_gedzip_sections() -> None:
    rules = _data_rules()
    datatypes = cast(dict[str, object], rules["datatypes"])
    assert set(datatypes) >= {
        "Age",
        "DateValue",
        "FilePath",
        "Language",
        "Latitude",
        "Longitude",
        "MediaType",
        "TagDef",
        "Time",
        "URI",
    }
    gedzip = cast(dict[str, object], rules["gedzip"])
    assert gedzip["dataset_entry"] == "gedcom.ged"
    assert gedzip["local_file_payloads_must_have_matching_entries"] is True
