"""Hard errors and exit code handling. Spec §9."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, cast


def _run_expect_exit1(command: tuple[str, ...], ics: str, tmp_path: Path) -> dict[str, Any]:
    ics_file = tmp_path / "in.ics"
    ics_file.write_bytes(ics.replace("\n", "\r\n").encode("utf-8"))
    output_file = tmp_path / "out.json"
    result = subprocess.run(
        [*command, "parse", "--input", str(ics_file), "--output", str(output_file)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1, f"expected exit 1, got {result.returncode}"
    assert output_file.exists()
    return cast(dict[str, Any], json.loads(output_file.read_text(encoding="utf-8")))


def test_unmatched_begin_end(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test//EN\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTART:20260305T100000Z\n"
        # Missing END:VEVENT
        "END:VCALENDAR\n"
    )
    out = _run_expect_exit1(submission_command, ics, tmp_path)
    assert "error" in out


def test_malformed_content_line(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test//EN\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTART:20260305T100000Z\n"
        "this_line_has_no_colon\n"
        "END:VEVENT\nEND:VCALENDAR\n"
    )
    out = _run_expect_exit1(submission_command, ics, tmp_path)
    assert "error" in out


def test_unclosed_vcalendar(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test//EN\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTART:20260305T100000Z\nEND:VEVENT\n"
        # Missing END:VCALENDAR
    )
    out = _run_expect_exit1(submission_command, ics, tmp_path)
    assert "error" in out


def test_error_has_line_message(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test//EN\nbroken_line\nEND:VCALENDAR\n"
    out = _run_expect_exit1(submission_command, ics, tmp_path)
    err = out["error"]
    assert isinstance(err["line"], int) and err["line"] >= 1
    assert isinstance(err["message"], str) and err["message"]


def test_invalid_expand_bounds(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test//EN\n"
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    ics_file = tmp_path / "in.ics"
    ics_file.write_bytes(ics.replace("\n", "\r\n").encode("utf-8"))
    output_file = tmp_path / "out.json"
    result = subprocess.run(
        [
            *submission_command,
            "expand",
            "--input",
            str(ics_file),
            "--from",
            "not-a-date",
            "--to",
            "2026-04-01T00:00:00Z",
            "--output",
            str(output_file),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
