from __future__ import annotations

import importlib.util
import json
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, cast

_REPO_ROOT = Path(__file__).resolve().parents[3]
_GENERATOR_PATH = _REPO_ROOT / "Evals" / "MARC21" / "scripts" / "generate_official_artifacts.py"
_RULES_PATH = (
    _REPO_ROOT
    / "Evals"
    / "MARC21"
    / "reference-implementation-py"
    / "generated"
    / "marc21_field_rules.json"
)
_EXAMPLES_PATH = (
    _REPO_ROOT / "Evals" / "MARC21" / "tests" / "generated" / "marc21_field_examples.json"
)
_FIXED_RULES_PATH = (
    _REPO_ROOT
    / "Evals"
    / "MARC21"
    / "reference-implementation-py"
    / "generated"
    / "marc21_fixed_field_rules.json"
)


def _load_generator_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("marc21_artifact_generator", _GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load generator module from {_GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_marc21_generated_artifacts_are_up_to_date() -> None:
    module = _load_generator_module()
    build_artifacts = cast(
        Callable[
            [],
            tuple[
                dict[str, dict[str, object]],
                dict[str, list[dict[str, str]]],
                dict[str, object],
            ],
        ],
        module.build_artifacts,
    )
    expected_rules, expected_examples, expected_fixed_rules = build_artifacts()
    actual_rules = cast(
        dict[str, dict[str, Any]], json.loads(_RULES_PATH.read_text(encoding="utf-8"))
    )
    actual_examples = cast(
        dict[str, list[dict[str, str]]], json.loads(_EXAMPLES_PATH.read_text(encoding="utf-8"))
    )
    actual_fixed_rules = cast(
        dict[str, Any], json.loads(_FIXED_RULES_PATH.read_text(encoding="utf-8"))
    )

    assert actual_rules == expected_rules
    assert actual_examples == expected_examples
    assert actual_fixed_rules == expected_fixed_rules
