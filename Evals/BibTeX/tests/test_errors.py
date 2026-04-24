"""Error handling: exit code 1 plus error JSON in --output."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, cast


def _run_for_exit1(
    command: tuple[str, ...], bib: str, style: str, cites: str, tmp_path: Path
) -> dict[str, Any]:
    bib_file = tmp_path / "refs.bib"
    bst_file = tmp_path / "style.bst"
    cites_file = tmp_path / "cites.txt"
    output_file = tmp_path / "out.json"
    bib_file.write_text(bib, encoding="utf-8")
    bst_file.write_text(style, encoding="utf-8")
    cites_file.write_text(cites, encoding="utf-8")
    result = subprocess.run(
        [
            *command,
            "--bib",
            str(bib_file),
            "--style",
            str(bst_file),
            "--cites",
            str(cites_file),
            "--output",
            str(output_file),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1, (
        f"expected exit 1, got {result.returncode}; stderr: {result.stderr}"
    )
    assert output_file.exists()
    return cast(dict[str, Any], json.loads(output_file.read_text(encoding="utf-8")))


MINIMAL_STYLE = """\
ENTRY { } { } { }
FUNCTION {f} { cite$ write$ newline$ }
READ
ITERATE {f}
"""


def test_malformed_bib_exits_1(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    out = _run_for_exit1(
        submission_command, "@article{k, title = {unclosed", MINIMAL_STYLE, "k\n", tmp_path
    )
    assert out["error"]["source"] == "bib"


def test_malformed_bst_exits_1(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    out = _run_for_exit1(
        submission_command,
        '@article{k, title = "x"}\n',
        'FUNCTION {broken} { "unterminated',  # unterminated string in .bst
        "k\n",
        tmp_path,
    )
    assert out["error"]["source"] == "bst"


def test_bst_unknown_command_exits_1(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    out = _run_for_exit1(
        submission_command,
        '@article{k, title = "x"}\n',
        "NOTACOMMAND { foo }\nREAD\n",
        "k\n",
        tmp_path,
    )
    assert out["error"]["source"] == "bst"


def test_error_object_has_line_column(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    out = _run_for_exit1(
        submission_command, "@article{k, title = {unclosed\n\nmore", MINIMAL_STYLE, "k\n", tmp_path
    )
    err = out["error"]
    assert "source" in err and "line" in err and "column" in err and "message" in err


def test_unknown_cli_flag_nonzero(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    result = subprocess.run(
        [*submission_command, "--not-a-real-flag"],
        capture_output=True,
        timeout=10,
    )
    assert result.returncode != 0
