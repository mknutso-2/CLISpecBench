from __future__ import annotations

import importlib.util
import json
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import cast

_REPO_ROOT = Path(__file__).resolve().parents[3]
_GENERATOR_PATH = _REPO_ROOT / "Evals" / "GEDCOM" / "scripts" / "generate_official_artifacts.py"
_STRUCTURES_PATH = (
    _REPO_ROOT / "Evals" / "GEDCOM" / "tests" / "generated" / "gedcom_structure_grammar.json"
)
_EXAMPLES_PATH = _REPO_ROOT / "Evals" / "GEDCOM" / "tests" / "generated" / "gedcom_examples.json"
_DATA_RULES_PATH = (
    _REPO_ROOT / "Evals" / "GEDCOM" / "tests" / "generated" / "gedcom_data_rules.json"
)


def _load_generator_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("gedcom_artifact_generator", _GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load generator module from {_GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gedcom_generated_artifacts_are_up_to_date() -> None:
    module = _load_generator_module()
    build_artifacts = cast(
        Callable[[], tuple[dict[str, str], list[dict[str, object]]]],
        module.build_artifacts,
    )
    expected_structures, expected_examples = build_artifacts()
    actual_structures = cast(
        dict[str, str],
        json.loads(_STRUCTURES_PATH.read_text(encoding="utf-8")),
    )
    actual_examples = cast(
        list[dict[str, object]],
        json.loads(_EXAMPLES_PATH.read_text(encoding="utf-8")),
    )

    assert actual_structures == expected_structures
    assert actual_examples == expected_examples


def test_gedcom_generated_data_rules_are_up_to_date() -> None:
    module = _load_generator_module()
    build_data_rules = cast(
        Callable[[], dict[str, object]],
        module.build_data_rules,
    )
    expected_rules = build_data_rules()
    actual_rules = cast(
        dict[str, object],
        json.loads(_DATA_RULES_PATH.read_text(encoding="utf-8")),
    )

    assert actual_rules == expected_rules


def test_gedcom_block_classifier_marks_full_dataset() -> None:
    module = _load_generator_module()
    classify_block = cast(
        Callable[[str, list[str], str | None], str],
        module._classify_gedcom_block,
    )

    assert classify_block("0 HEAD\n1 GEDC\n0 TRLR", [], None) == "dataset"
    assert (
        classify_block(
            "0 @BAD@ INDI\n1 RESN PARENT",
            ["example"],
            "The following is not allowed because PARENT is defined for ROLE, not RESN.",
        )
        == "counterexample"
    )
    assert (
        classify_block(
            "1 SCHEMA\n2 TAG _LANG https://gedcom.io/terms/v7/LANG",
            ["note"],
            None,
        )
        == "note"
    )
    assert classify_block("0 @I1@ INDI\n1 NAME John /Doe/", [], "Provides no new information.") == (
        "record_fragment"
    )
    assert classify_block("1 NAME John /Doe/", [], "Provides no new information.") == (
        "substructure_fragment"
    )
