"""Schema gate: assert the top-level shape of each subcommand's JSON output.

This file is the ``skills/eval-authoring/SKILL.md`` "single schema
gate" for the IGES eval. A missing or misnamed top-level field is a
schema failure that belongs here, not in every behavioral test. By
centralizing the schema shape in a handful of assertions, downstream
behavioral tests can use ``.get()`` for tolerant access and surface as
"behavior X is wrong" rather than as a cascade of ``KeyError``s.

The envelope shapes asserted here are defined in
``Evals/IGES/prompt/technical-requirements-prompt.md`` §1.3–§1.5 and §2.2.
"""
# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from iges_support import (
    make_entity,
    parse_iges_to_json,
    query_entity,
    wrap_entities,
    write_iges_from_json,
)


def _simple_line_document() -> dict[str, object]:
    return wrap_entities([
        make_entity(
            de_index=1,
            entity_type=110,
            data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
        ),
    ])


def _eval_curve(
    submission_command: Sequence[str],
    iges_path: Path,
    tmp_path: Path,
    de: int,
    t: float,
) -> dict[str, object]:
    out = tmp_path / "eval.json"
    subprocess.run(
        [
            *submission_command,
            "eval",
            "--input", str(iges_path),
            "--de", str(de),
            "--t", str(t),
            "--output", str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return json.loads(out.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# `iges parse` — success envelope
# ---------------------------------------------------------------------------


def test_parse_success_envelope_has_required_top_level_keys(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """§2.2: parse success output has `start_lines`, `global`, `entities`.

    Also asserts the EntityRecord shape (§2.5): each entry has
    `directory_entry`, `entity`, and `de_index`. Downstream behavioral
    tests assume this shape.
    """
    iges_path = write_iges_from_json(
        submission_command, _simple_line_document(), tmp_path,
    )
    parsed = parse_iges_to_json(submission_command, iges_path, tmp_path)

    assert isinstance(parsed, dict), "parse output must be a JSON object"
    assert "start_lines" in parsed, "parse output missing `start_lines`"
    assert "global" in parsed, "parse output missing `global`"
    assert "entities" in parsed, "parse output missing `entities`"
    assert isinstance(parsed["start_lines"], list)
    assert isinstance(parsed["global"], dict)
    assert isinstance(parsed["entities"], list)
    assert len(parsed["entities"]) >= 1, "entities list must not be empty"

    entity_record = parsed["entities"][0]
    assert isinstance(entity_record, dict)
    assert "directory_entry" in entity_record, \
        "EntityRecord missing `directory_entry`"
    assert "entity" in entity_record, "EntityRecord missing `entity`"
    assert "de_index" in entity_record, "EntityRecord missing `de_index`"


def test_parse_global_section_has_required_keys(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """§2.3: Global section has the 26 required fields (spot-check a few)."""
    iges_path = write_iges_from_json(
        submission_command, _simple_line_document(), tmp_path,
    )
    parsed = parse_iges_to_json(submission_command, iges_path, tmp_path)
    global_section = parsed.get("global", {})

    required = [
        "param_delimiter", "record_delimiter", "product_id_sender",
        "file_name", "native_system_id", "preprocessor_version",
        "integer_bits", "sp_magnitude", "sp_significance",
        "dp_magnitude", "dp_significance", "model_space_scale",
        "units", "units_name", "file_timestamp", "min_resolution",
    ]
    missing = [k for k in required if k not in global_section]
    assert missing == [], f"Global section missing required keys: {missing}"


# ---------------------------------------------------------------------------
# `iges parse` — error envelope
# ---------------------------------------------------------------------------


def test_parse_error_envelope_has_required_top_level_keys(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """§1.4: error envelope has `ok` (false), `error`, `spec_ref`, `line`,
    `section`, `diagnostics`.
    """
    iges_path = tmp_path / "bad.iges"
    iges_path.write_text("not an iges file at all\n", encoding="latin-1")
    out = tmp_path / "bad.json"
    completed = subprocess.run(
        [
            *submission_command,
            "parse",
            "--input", str(iges_path),
            "--output", str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 1, "non-IGES input must exit 1"
    payload = json.loads(out.read_text(encoding="utf-8"))

    assert isinstance(payload, dict)
    assert payload.get("ok") is False
    assert "error" in payload, "error envelope missing `error`"
    assert "spec_ref" in payload, "error envelope missing `spec_ref`"
    assert "line" in payload, "error envelope missing `line`"
    assert "section" in payload, "error envelope missing `section`"
    assert "diagnostics" in payload, "error envelope missing `diagnostics`"
    assert isinstance(payload["error"], str)
    assert isinstance(payload["diagnostics"], list)


# ---------------------------------------------------------------------------
# `iges eval` — success envelope
# ---------------------------------------------------------------------------


def test_eval_success_envelope_has_required_top_level_keys(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """§1.5: eval success output has `ok` (true), `point`, `tangent`,
    `normal`, `error`.
    """
    iges_path = write_iges_from_json(
        submission_command, _simple_line_document(), tmp_path,
    )
    payload = _eval_curve(submission_command, iges_path, tmp_path, de=1, t=0.5)

    assert isinstance(payload, dict)
    assert payload.get("ok") is True
    assert "point" in payload, "eval output missing `point`"
    assert "tangent" in payload, "eval output missing `tangent` (may be null)"
    assert "normal" in payload, "eval output missing `normal` (may be null)"
    assert "error" in payload, "eval output missing `error` (may be null)"
    assert payload["error"] is None, \
        "eval success envelope must carry `error: null` per §1.5"
    assert isinstance(payload["point"], list)
    assert len(payload["point"]) == 3


# ---------------------------------------------------------------------------
# `iges query` — success envelope
# ---------------------------------------------------------------------------


def test_query_success_envelope_has_entity_keys(
    submission_command: Sequence[str], tmp_path: Path,
) -> None:
    """§2.5: query returns a single EntityRecord with `directory_entry`,
    `entity`, and `de_index`.
    """
    iges_path = write_iges_from_json(
        submission_command, _simple_line_document(), tmp_path,
    )
    entity = query_entity(submission_command, iges_path, 1, tmp_path)

    assert isinstance(entity, dict)
    assert "directory_entry" in entity, "query output missing `directory_entry`"
    assert "entity" in entity, "query output missing `entity`"
    assert "de_index" in entity, "query output missing `de_index`"
