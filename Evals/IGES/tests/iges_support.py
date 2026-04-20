"""Test helpers for the IGES eval.

These helpers drive the `iges` CLI end-to-end: tests typically build
canonical IGES-JSON in Python, shell out to ``iges write`` to produce a
.iges file, then exercise ``iges parse``/``query``/``eval``/``roundtrip``
and assert on the JSON output.

The CLI contract (five subcommands, exit codes 0/1/2, envelope shape) is
specified in ``Evals/IGES/prompt/technical-requirements-prompt.md``.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Canonical IGES-JSON builders
# ---------------------------------------------------------------------------

Vec3 = tuple[float, float, float]


def default_global() -> dict[str, Any]:
    """Return a Global section dict with IGES-spec-legal defaults.

    All 26 fields per §2.2.4.3.  Tests override individual fields as needed.
    """
    return {
        "param_delimiter": ",",
        "record_delimiter": ";",
        "product_id_sender": "TEST",
        "file_name": "test.iges",
        "native_system_id": "PYTEST",
        "preprocessor_version": "PYTEST",
        "integer_bits": 32,
        "sp_magnitude": 38,
        "sp_significance": 7,
        "dp_magnitude": 308,
        "dp_significance": 15,
        "product_id_receiver": "TEST",
        "model_space_scale": 1.0,
        "units": "inches",
        "units_name": "INCH",
        "max_line_weight_grads": 1,
        "max_line_weight_width": 0.01,
        "file_timestamp": {
            "year": 2026,
            "month": 4,
            "day": 14,
            "hour": 12,
            "minute": 0,
            "second": 0,
        },
        "min_resolution": 0.001,
        "max_coordinate": 1000.0,
        "author": "pytest",
        "organization": "clispecbench",
        "spec_version": "v5_3",
        "drafting_std": "none",
        "model_timestamp": None,
        "app_protocol": "",
    }


def default_directory_entry(
    entity_type: int,
    *,
    form: int = 0,
    param_data_ptr: int = 1,
    param_line_count: int = 1,
    structure: int = 0,
    line_font: int = 0,
    level: int = 0,
) -> dict[str, Any]:
    """Return a DirectoryEntry dict with reasonable defaults.

    See §2.2.4.4 for the 20 fields.  The canonical JSON flattens fields
    10/20 (derived) and 11 (mirror of field 1); the remaining 15 live here.
    """
    return {
        "entity_type": entity_type,
        "param_data_ptr": param_data_ptr,
        "structure": structure,
        "line_font": line_font,
        "level": level,
        "view": 0,
        "xform_matrix": 0,
        "label_display": 0,
        "status": {
            "blank": "visible",
            "subordinate": "independent",
            "entity_use": "geometry",
            "hierarchy": "global_top_down",
        },
        "line_weight": 0,
        "color": 0,
        "param_line_count": param_line_count,
        "form": form,
        "entity_label": "",
        "entity_subscript": 0,
    }


def wrap_entities(entities: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Assemble a full canonical IGES-JSON document around a list of entities.

    Each entry in ``entities`` must already include ``de_index``,
    ``directory_entry``, and ``entity`` keys (use :func:`make_entity`).
    """
    return {
        "start_lines": ["pytest-generated IGES fixture"],
        "global": default_global(),
        "entities": list(entities),
    }


def make_entity(
    *,
    de_index: int,
    entity_type: int,
    form: int = 0,
    data: Mapping[str, Any],
    directory_entry_overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one ``entities[]`` record with matching DE + data payload."""
    de = default_directory_entry(entity_type, form=form)
    if directory_entry_overrides is not None:
        de.update(directory_entry_overrides)
    return {
        "de_index": de_index,
        "directory_entry": de,
        "entity": {
            "type": entity_type,
            "form": form,
            "data": dict(data),
        },
    }


def single_line_document(start: Vec3, terminate: Vec3) -> dict[str, Any]:
    """Convenience: a file containing exactly one Type 110 Line entity."""
    return wrap_entities([
        make_entity(
            de_index=1,
            entity_type=110,
            data={"start": list(start), "terminate": list(terminate)},
        ),
    ])


# ---------------------------------------------------------------------------
# CLI drivers
# ---------------------------------------------------------------------------


def _run_cli(
    submission_command: Sequence[str],
    *args: str,
    check: bool = True,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    cmd = [*submission_command, *args]
    completed = subprocess.run(
        cmd,
        capture_output=True,
        check=False,
        text=True,
        timeout=timeout,
    )
    if check and completed.returncode != 0:
        raise AssertionError(
            f"iges CLI failed (exit {completed.returncode}):\n"
            f"  cmd: {cmd}\n"
            f"  stdout: {completed.stdout}\n"
            f"  stderr: {completed.stderr}\n"
        )
    return completed


def write_iges_from_json(
    submission_command: Sequence[str],
    document: Mapping[str, Any],
    tmp_path: Path,
    *,
    name: str = "out",
) -> Path:
    """Write ``document`` to JSON, then invoke ``iges write`` to get a .iges."""
    json_path = tmp_path / f"{name}.json"
    iges_path = tmp_path / f"{name}.iges"
    json_path.write_text(json.dumps(document), encoding="utf-8")
    _run_cli(
        submission_command,
        "write",
        "--input", str(json_path),
        "--output", str(iges_path),
    )
    assert iges_path.is_file(), "iges write did not produce an output file"
    return iges_path


def parse_iges_to_json(
    submission_command: Sequence[str],
    iges_path: Path,
    tmp_path: Path,
    *,
    name: str = "parsed",
) -> dict[str, Any]:
    out = tmp_path / f"{name}.json"
    _run_cli(
        submission_command,
        "parse",
        "--input", str(iges_path),
        "--output", str(out),
    )
    return json.loads(out.read_text(encoding="utf-8"))


def query_entity(
    submission_command: Sequence[str],
    iges_path: Path,
    de_index: int,
    tmp_path: Path,
    *,
    name: str = "query",
) -> dict[str, Any]:
    out = tmp_path / f"{name}.json"
    _run_cli(
        submission_command,
        "query",
        "--input", str(iges_path),
        "--de", str(de_index),
        "--output", str(out),
    )
    return json.loads(out.read_text(encoding="utf-8"))


def evaluate_entity(
    submission_command: Sequence[str],
    iges_path: Path,
    de_index: int,
    t: float,
    tmp_path: Path,
    *,
    s: float | None = None,
    name: str = "eval",
    check: bool = True,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    out = tmp_path / f"{name}.json"
    args = [
        "eval",
        "--input", str(iges_path),
        "--de", str(de_index),
        "--t", repr(t),
        "--output", str(out),
    ]
    if s is not None:
        args.extend(["--s", repr(s)])
    completed = _run_cli(submission_command, *args, check=check)
    payload = json.loads(out.read_text(encoding="utf-8"))
    return completed, payload


def roundtrip_iges(
    submission_command: Sequence[str],
    iges_path: Path,
    tmp_path: Path,
    *,
    name: str = "rt",
) -> Path:
    out = tmp_path / f"{name}.iges"
    _run_cli(
        submission_command,
        "roundtrip",
        "--input", str(iges_path),
        "--output", str(out),
    )
    return out


def semantic_roundtrip_json(
    submission_command: Sequence[str],
    document: Mapping[str, Any],
    tmp_path: Path,
) -> dict[str, Any]:
    """JSON → write → parse → JSON.

    Returns the reparsed canonical JSON, which should be ``entity.data``-
    equivalent to the input document (see §2 canonical-JSON schema).
    """
    iges_path = write_iges_from_json(submission_command, document, tmp_path)
    return parse_iges_to_json(submission_command, iges_path, tmp_path)
