from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, cast

from clispecbench.pytest_plugin import (
    EvalConfig,
    build_timeout_seconds,
    eval_language,
    language_target,
    prepared_submission,
    pytest_addoption,
    repo_root,
    submission_command,
)

__all__ = [
    "EvalConfig",
    "build_timeout_seconds",
    "eval_language",
    "language_target",
    "prepared_submission",
    "pytest_addoption",
    "repo_root",
    "submission_command",
]

EVAL_CONFIG = EvalConfig(
    task_name="ical",
    reference_impl_subdirs={
        "cpp": "Evals/ICal/reference-implementation-cpp",
    },
    env_var="CLISPECBENCH_ICAL_ROOT",
    preferred_executable_name="ical",
)


def _run_tool(
    command: tuple[str, ...],
    args: list[str],
    tmp_path: Path,
    *,
    timeout: int = 30,
    expect_exit: int = 0,
) -> dict[str, Any]:
    output_file = tmp_path / "out.json"
    result = subprocess.run(
        [*command, *args, "--output", str(output_file)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    assert result.returncode == expect_exit, (
        f"ical exited with {result.returncode} (expected {expect_exit})\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert output_file.exists(), "output file was not created"
    return cast(dict[str, Any], json.loads(output_file.read_text(encoding="utf-8")))


def run_parse(
    command: tuple[str, ...],
    ics: str,
    tmp_path: Path,
    *,
    timeout: int = 30,
    expect_exit: int = 0,
) -> dict[str, Any]:
    ics_file = tmp_path / "in.ics"
    # Ensure CRLF line endings per RFC 5545.
    normalized = ics.replace("\r\n", "\n").replace("\n", "\r\n")
    ics_file.write_bytes(normalized.encode("utf-8"))
    return _run_tool(
        command,
        ["parse", "--input", str(ics_file)],
        tmp_path,
        timeout=timeout,
        expect_exit=expect_exit,
    )


def run_expand(
    command: tuple[str, ...],
    ics: str,
    from_: str,
    to_: str,
    tmp_path: Path,
    *,
    timeout: int = 30,
    expect_exit: int = 0,
) -> dict[str, Any]:
    ics_file = tmp_path / "in.ics"
    normalized = ics.replace("\r\n", "\n").replace("\n", "\r\n")
    ics_file.write_bytes(normalized.encode("utf-8"))
    return _run_tool(
        command,
        ["expand", "--input", str(ics_file), "--from", from_, "--to", to_],
        tmp_path,
        timeout=timeout,
        expect_exit=expect_exit,
    )


def find_event(payload: dict[str, Any], uid: str) -> dict[str, Any]:
    events = payload.get("events")
    if not isinstance(events, list):
        raise AssertionError(f"output has no 'events' array (top-level keys: {list(payload)})")
    for raw in cast(list[Any], events):
        if isinstance(raw, dict):
            ev = cast(dict[str, Any], raw)
            if ev.get("uid") == uid:
                return ev
    raise AssertionError(f"event with uid {uid!r} not found in output")


def warnings_of(payload: dict[str, Any]) -> list[dict[str, Any]]:
    w = payload.get("warnings")
    if isinstance(w, list):
        return cast(list[dict[str, Any]], w)
    return []


def occurrences_of(payload: dict[str, Any]) -> list[dict[str, Any]]:
    occs = payload.get("occurrences")
    if isinstance(occs, list):
        return cast(list[dict[str, Any]], occs)
    return []


def starts_for(occurrences: list[dict[str, Any]], uid: str) -> list[str]:
    return [cast(str, o.get("dtstart")) for o in occurrences if o.get("uid") == uid]


BASIC_HEADER = """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
"""

BASIC_FOOTER = "END:VCALENDAR\n"


def wrap_event(body: str) -> str:
    """Wrap a VEVENT body in a minimal VCALENDAR."""
    return BASIC_HEADER + "BEGIN:VEVENT\n" + body + "END:VEVENT\n" + BASIC_FOOTER
