"""Error-envelope shape tests for parse / query / eval.

TR §1.4 specifies the error JSON shape emitted to ``--output`` on failure.
Existing negative tests (test_malformed.py, test_validation.py, etc.)
assert only ``ok`` and ``error``; these tests add shape coverage for the
three remaining top-level fields (``spec_ref``, ``line``, ``section``)
and the ``diagnostics`` array.

Scope: parse / query / eval only. ``write`` and ``roundtrip`` emit error
JSON to stderr (not ``--output``), so their envelope is out of scope —
see IGES-PROPOSED-CHANGES-MERGED.md §1 note.

Type-level assertions rather than enum checks: the TR vocabulary for
``section`` ("S"/"G"/...) and the reference implementation's vocabulary
("start"/"directory"/...) currently disagree; these tests lock in the
shape without forcing a particular vocabulary.
"""

# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from iges_support import (
    make_entity,
    single_line_document,
    wrap_entities,
    write_iges_from_json,
)


def _assert_envelope_shape(payload: Mapping[str, Any]) -> None:
    """Assert the five TR §1.4 top-level fields plus the diagnostics list shape."""
    assert "ok" in payload, f"envelope missing 'ok': {payload}"
    assert payload["ok"] is False

    assert "error" in payload
    assert isinstance(payload["error"], str)
    assert payload["error"], "error message must be non-empty"

    assert "spec_ref" in payload
    assert payload["spec_ref"] is None or isinstance(payload["spec_ref"], str)

    assert "line" in payload
    assert payload["line"] is None or isinstance(payload["line"], int)

    assert "section" in payload
    # TR §1.4 declares "S"|"G"|"D"|"P"|"T"|null; ref-impl emits
    # "start"|"global"|... ; either vocabulary is accepted here.
    assert payload["section"] is None or isinstance(payload["section"], str)

    assert "diagnostics" in payload
    assert isinstance(payload["diagnostics"], list)
    for diag in payload["diagnostics"]:
        assert isinstance(diag, dict)
        assert "severity" in diag
        assert diag["severity"] in ("info", "warning", "error")
        assert "message" in diag and isinstance(diag["message"], str)
        assert "spec_ref" in diag
        assert diag["spec_ref"] is None or isinstance(diag["spec_ref"], str)
        assert "line" in diag
        assert diag["line"] is None or isinstance(diag["line"], int)
        assert "section" in diag
        assert diag["section"] is None or isinstance(diag["section"], str)


def test_parse_error_envelope_has_all_required_fields(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    iges_path = tmp_path / "garbage.iges"
    iges_path.write_bytes(b"not an IGES file\n")
    out = tmp_path / "err.json"
    completed = subprocess.run(
        [
            *submission_command,
            "parse",
            "--input",
            str(iges_path),
            "--output",
            str(out),
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    _assert_envelope_shape(payload)


def test_query_error_envelope_has_all_required_fields(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = single_line_document((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    out = tmp_path / "err.json"
    completed = subprocess.run(
        [
            *submission_command,
            "query",
            "--input",
            str(iges_path),
            "--de",
            "999",
            "--output",
            str(out),
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    _assert_envelope_shape(payload)


def test_eval_error_envelope_has_all_required_fields(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    # Property (406) is non-parametric; eval must reject it.
    doc = wrap_entities(
        [
            make_entity(
                de_index=1,
                entity_type=406,
                data={"np": 1, "values": [{"kind": "real", "value": 1.0}]},
            ),
        ]
    )
    iges_path = write_iges_from_json(submission_command, doc, tmp_path)
    out = tmp_path / "err.json"
    completed = subprocess.run(
        [
            *submission_command,
            "eval",
            "--input",
            str(iges_path),
            "--de",
            "1",
            "--t",
            "0.0",
            "--output",
            str(out),
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    _assert_envelope_shape(payload)
