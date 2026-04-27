"""Malformed-input tests — the CLI must exit non-zero with a JSON
diagnostic, never crash.

Ports the CLI-observable subset of the SDK's ``test_malformed.cpp``
MAL-1..MAL-12 cases. The library-level tests (ParamTokenizer, lexer,
directory_entry parse) aren't portable to a CLI harness; we cover the
same surface by asserting that ``iges parse`` rejects malformed .iges
files with exit code 1 and a diagnostic envelope.

Envelope contract (see ``prompt/technical-requirements-prompt.md``):

    {"ok": false, "error": "...", "spec_ref": "§X.Y",
     "line": N, "section": "...",
     "diagnostics": [ { ... } ]}

We assert on ``ok == false`` and the presence of an ``error`` field.
Exact spec_ref / line values are implementation-dependent and not
asserted — the point is that the failure is reported, not silenced.
"""

# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from iges_support import make_entity, wrap_entities, write_iges_from_json


def _run_parse_expecting_failure(
    submission_command: Sequence[str],
    iges_path: Path,
    output_path: Path,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        *submission_command,
        "parse",
        "--input",
        str(iges_path),
        "--output",
        str(output_path),
    ]
    return subprocess.run(
        cmd,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )


def _pad80(s: str, section: str, seq: int) -> str:
    """Right-pad ``s`` to 72 chars, then append section letter + 7-digit seq."""
    body = s.ljust(72)[:72]
    return f"{body}{section}{seq:>7d}"


def _minimal_valid_iges() -> str:
    """Construct a byte-clean minimal IGES document: S/G/D/P/T with no
    entities. Built to mirror the SDK's make_minimal_file() helper."""
    # S section — one comment line.
    s = _pad80("pytest fixture", "S", 1)
    # G section — compact single line with all 26 fields defaulted.
    g_body = (
        "1H,,1H;,4Htest,8Htest.igs,3HSDK,3H1.0,32,38,6,308,15,,1.0,"
        "2,2HMM,1,0.01,15H20260414.120000,1.0E-6,1.0,3Husr,4Hsite,11,3,;"
    )
    g_lines: list[str] = []
    for i in range(0, len(g_body), 72):
        chunk = g_body[i : i + 72]
        g_lines.append(_pad80(chunk, "G", len(g_lines) + 1))
    # T section — no entities, so D/P totals are zero.
    t_body = f"S{1:>7d}G{len(g_lines):>7d}D{0:>7d}P{0:>7d}"
    t = _pad80(t_body, "T", 1)
    return "\n".join([s, *g_lines, t]) + "\n"


def _write(p: Path, s: str) -> None:
    p.write_bytes(s.encode("ascii"))


# MAL-1: no Start section
def test_file_without_start_section_is_rejected(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    iges = tmp_path / "no_start.iges"
    # Only a G line + T line, no S line.
    g_line = _pad80(
        "1H,,1H;,4Htest,8Htest.igs,3HSDK,3H1.0,32,38,6,308,15,,1.0,"
        "2,2HMM,1,0.01,15H20260414.120000,1.0E-6,1.0,3Hx,3Hy,11,3,;",
        "G",
        1,
    )
    t_line = _pad80(f"S{0:>7d}G{1:>7d}D{0:>7d}P{0:>7d}", "T", 1)
    _write(iges, g_line + "\n" + t_line + "\n")

    completed = _run_parse_expecting_failure(submission_command, iges, tmp_path / "out.json")
    assert completed.returncode == 1
    payload = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert payload.get("ok") is False
    assert "error" in payload


# MAL-2: empty file / no sections
def test_empty_file_is_rejected(submission_command: Sequence[str], tmp_path: Path) -> None:
    iges = tmp_path / "empty.iges"
    iges.write_bytes(b"")
    completed = _run_parse_expecting_failure(submission_command, iges, tmp_path / "out.json")
    assert completed.returncode == 1
    payload = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert payload.get("ok") is False


# MAL-12: truncated file — no T section
def test_truncated_file_is_rejected(submission_command: Sequence[str], tmp_path: Path) -> None:
    iges = tmp_path / "truncated.iges"
    # S + G, then abrupt end (no T section).
    s = _pad80("truncated", "S", 1)
    g = _pad80(
        "1H,,1H;,4Htest,8Htest.igs,3HSDK,3H1.0,32,38,6,308,15,,1.0,"
        "2,2HMM,1,0.01,15H20260414.120000,1.0E-6,1.0,3Hx,3Hy,11,3,;",
        "G",
        1,
    )
    _write(iges, s + "\n" + g + "\n")

    completed = _run_parse_expecting_failure(submission_command, iges, tmp_path / "out.json")
    # TR §1.2: missing Terminate section is invalid input → exit 1.
    assert completed.returncode == 1
    payload = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert payload.get("ok") is False
    assert "error" in payload


# MAL-10: valid minimal file with no entities parses cleanly.
def test_minimal_valid_file_parses(submission_command: Sequence[str], tmp_path: Path) -> None:
    iges = tmp_path / "minimal.iges"
    _write(iges, _minimal_valid_iges())

    completed = _run_parse_expecting_failure(submission_command, iges, tmp_path / "out.json")
    # This one is supposed to succeed; the helper name is a misnomer here.
    assert completed.returncode == 0, completed.stderr
    payload = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    # We expect the canonical IGES-JSON envelope (not the error envelope).
    assert "entities" in payload
    assert payload.get("entities") == []


# MAL: query with out-of-range DE index
def test_query_with_nonexistent_de_is_rejected(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    iges = tmp_path / "minimal.iges"
    _write(iges, _minimal_valid_iges())
    out = tmp_path / "query.json"
    cmd = [
        *submission_command,
        "query",
        "--input",
        str(iges),
        "--de",
        "999",
        "--output",
        str(out),
    ]
    completed = subprocess.run(
        cmd,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    # TR §1.2: out-of-range DE is invalid input → exit 1.
    assert completed.returncode == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload.get("ok") is False


# TR §1.2: "query --de <n> on an out-of-range or even DE index is invalid
# input (exit code 1)". The out-of-range case is covered above; this
# exercises the even-DE branch against a file with enough entities that
# DE 2 is not also out-of-range (it's the second physical line of the
# first entity's DE record, not a standalone odd DE).
def test_query_with_even_de_is_rejected(submission_command: Sequence[str], tmp_path: Path) -> None:
    doc = wrap_entities(
        [
            make_entity(
                de_index=1,
                entity_type=110,
                data={"start": [0.0, 0.0, 0.0], "terminate": [1.0, 0.0, 0.0]},
            ),
            make_entity(
                de_index=3,
                entity_type=110,
                data={"start": [1.0, 0.0, 0.0], "terminate": [2.0, 0.0, 0.0]},
            ),
        ]
    )
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="even-de")
    out = tmp_path / "query-even.json"
    cmd = [
        *submission_command,
        "query",
        "--input",
        str(iges_path),
        "--de",
        "2",
        "--output",
        str(out),
    ]
    completed = subprocess.run(
        cmd,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload.get("ok") is False


# MAL: garbage file (not IGES at all)
def test_random_bytes_are_rejected(submission_command: Sequence[str], tmp_path: Path) -> None:
    iges = tmp_path / "garbage.iges"
    iges.write_bytes(b"This is not an IGES file, it is a haiku.\n")
    completed = _run_parse_expecting_failure(submission_command, iges, tmp_path / "out.json")
    assert completed.returncode == 1
    payload = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert payload.get("ok") is False
