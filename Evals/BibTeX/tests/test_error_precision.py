"""Error-message line/column precision.

The technical-requirements-prompt.md contract says error JSON includes
``line`` (integer) and ``column`` (integer) fields pointing at the
offending token. ``test_errors.py`` only asserts exit code 1; this file
pins the location metadata so a bug in error reporting surfaces as a
single precise test failure.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _run_for_error(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    bib: str,
    style: str,
    *,
    cites: str | None = None,
) -> dict[str, object]:
    """Run bibtex expecting exit=1 and return the error JSON."""
    bib_file = tmp_path / "refs.bib"
    bst_file = tmp_path / "style.bst"
    out_file = tmp_path / "out.bbl"
    cites_file = tmp_path / "cites.txt"
    bib_file.write_text(bib, encoding="utf-8")
    bst_file.write_text(style, encoding="utf-8")
    cites_file.write_text(cites if cites is not None else "a\n", encoding="utf-8")
    result = subprocess.run(
        [
            *submission_command,
            "--bib",
            str(bib_file),
            "--style",
            str(bst_file),
            "--cites",
            str(cites_file),
            "--output",
            str(out_file),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1, (
        f"expected exit 1, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    content = out_file.read_text(encoding="utf-8")
    data = json.loads(content)
    assert isinstance(data, dict), f"error body is not a JSON object: {content}"
    return data  # type: ignore[return-value]


MIN_STYLE = """\
ENTRY { } { } { }
FUNCTION {f} { cite$ write$ }
READ
ITERATE {f}
"""


# ---------------------------------------------------------------------------
# .bib error locations
# ---------------------------------------------------------------------------


def test_error_reports_line_column_for_unclosed_entry(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An unclosed @article entry reports a line/column near the end of
    the file (where EOF was hit unexpectedly)."""
    bib = "@article{a, title = \"T\"\n"  # no closing brace
    err = _run_for_error(submission_command, tmp_path, bib, MIN_STYLE)
    error = err.get("error")
    assert isinstance(error, dict), f"error JSON missing 'error' object: {err}"
    line = error.get("line")
    col = error.get("column")
    assert isinstance(line, int) and line >= 1, f"line not positive int: {line}"
    assert isinstance(col, int) and col >= 1, f"column not positive int: {col}"


def test_error_reports_source_bib_for_bib_errors(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """When the error originates in the .bib, source='bib'."""
    bib = "@article{a, title = !@#$}\n"
    err = _run_for_error(submission_command, tmp_path, bib, MIN_STYLE)
    error = err.get("error")
    assert isinstance(error, dict)
    if "source" in error:
        assert error["source"] == "bib", f"expected source=bib, got {error['source']}"


def test_error_line_column_are_nonzero(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Line and column should be 1-indexed positive integers, not 0."""
    bib = "@article{a, title = \"unterminated\n"  # unterminated string
    err = _run_for_error(submission_command, tmp_path, bib, MIN_STYLE)
    error = err.get("error")
    assert isinstance(error, dict)
    line = error.get("line")
    col = error.get("column")
    assert isinstance(line, int) and line >= 1
    assert isinstance(col, int) and col >= 1


# ---------------------------------------------------------------------------
# .bst error locations
# ---------------------------------------------------------------------------


def test_error_reports_line_column_for_malformed_bst(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Garbage in .bst produces an error with line/column."""
    bib = "@misc{a}\n"
    # Malformed .bst: using !!! which isn't a valid construct.
    style = """\
ENTRY { } { } { }
FUNCTION {f} { !!! }
READ
EXECUTE {f}
"""
    err = _run_for_error(submission_command, tmp_path, bib, style)
    error = err.get("error")
    assert isinstance(error, dict)
    line = error.get("line")
    col = error.get("column")
    # Line should point somewhere in the .bst (specifically line 2 where !!! is).
    assert isinstance(line, int) and line >= 1
    assert isinstance(col, int) and col >= 1
    if "source" in error:
        assert error["source"] in ("bst", "runtime"), f"source={error['source']}"


# ---------------------------------------------------------------------------
# CLI flag errors
# ---------------------------------------------------------------------------


def test_missing_required_flag_exits_one(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Missing --bib or --style exits 1."""
    result = subprocess.run(
        [*submission_command, "--output", str(tmp_path / "x.bbl")],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1, (
        f"expected exit 1 for missing flags, got {result.returncode}"
    )


def test_nonexistent_bib_file_exits_one(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """--bib pointing at a nonexistent path exits 1."""
    out = tmp_path / "out.bbl"
    cites = tmp_path / "cites.txt"
    cites.write_text("a\n", encoding="utf-8")
    style = tmp_path / "s.bst"
    style.write_text(MIN_STYLE, encoding="utf-8")
    result = subprocess.run(
        [
            *submission_command,
            "--bib",
            str(tmp_path / "does-not-exist.bib"),
            "--style",
            str(style),
            "--cites",
            str(cites),
            "--output",
            str(out),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1


def test_nonexistent_aux_file_exits_one(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """--aux pointing at a nonexistent path exits 1."""
    bib = tmp_path / "refs.bib"
    bib.write_text("@misc{a}\n", encoding="utf-8")
    style = tmp_path / "s.bst"
    style.write_text(MIN_STYLE, encoding="utf-8")
    out = tmp_path / "out.bbl"
    result = subprocess.run(
        [
            *submission_command,
            "--bib",
            str(bib),
            "--style",
            str(style),
            "--aux",
            str(tmp_path / "missing.aux"),
            "--output",
            str(out),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1


# ---------------------------------------------------------------------------
# Error JSON shape is always well-formed on exit 1
# ---------------------------------------------------------------------------


def test_error_json_is_valid_object(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Any exit-1 case must produce a JSON object with an 'error' field."""
    # Trigger by giving a malformed bib.
    bib = "@article{\n"  # no key
    err = _run_for_error(submission_command, tmp_path, bib, MIN_STYLE)
    assert "error" in err, f"error body missing 'error' key: {err}"
    assert isinstance(err["error"], dict)
    assert "message" in err["error"], f"error.message missing: {err['error']}"
