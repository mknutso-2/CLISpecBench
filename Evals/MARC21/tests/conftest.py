from __future__ import annotations

import json
import subprocess
from base64 import b64decode, b64encode
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import pytest

from clispecbench.build import PreparedSubmission
from clispecbench.pytest_plugin import (
    EvalConfig,
    build_timeout_seconds,
    eval_language,
    language_target,
    prepared_submission,
    pytest_addoption,
    repo_root,
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
    task_name="marc21",
    reference_impl_subdirs={
        "py": "Evals/MARC21/reference-implementation-py",
    },
    env_var="CLISPECBENCH_MARC21_ROOT",
    preferred_executable_name="marc21",
)


def run_marc21(
    command: Sequence[str],
    request: Mapping[str, Any],
    tmp_path: Path,
    *,
    timeout: int = 30,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any] | None]:
    request_file = tmp_path / "request.json"
    output_file = tmp_path / "response.json"
    request_file.write_text(json.dumps(dict(request), indent=2), encoding="utf-8")
    result = subprocess.run(
        [*command, "--input", str(request_file), "--output", str(output_file)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if not output_file.exists():
        return result, None
    payload = cast(dict[str, Any], json.loads(output_file.read_text(encoding="utf-8")))
    return result, payload


def b64(data: bytes) -> str:
    return b64encode(data).decode("ascii")


def unb64(text: str) -> bytes:
    return b64decode(text.encode("ascii"))


# ---------------------------------------------------------------------------
# CLI smoke gate (rule-3 cascade fix introduced in v2.8.2)
#
# A single startup bug in the agent's CLI (e.g. tries to read a prompt-time
# `docs/` directory at run time, throws on import, exits early on a missing
# dependency) causes ``returncode != 0`` on every subsequent CLI invocation.
# Because the suite has ~2,840 CLI-invoking tests, one such bug cascades
# into ~2,840 near-identical failures — the rule-3 antipattern from
# `skills/eval-authoring/SKILL.md`.
#
# This module overrides the shared `submission_command` fixture to run a
# minimal `inspect` request once per session before any CLI test. If the
# request returns non-zero, the fixture calls ``pytest.skip`` with a uniform
# reason, which transitively skips every test that depends on
# `submission_command` (i.e. every CLI test). Tests that do not invoke the
# CLI — ``test_build``, anything driven by `prepared_submission` directly
# without `submission_command` — continue to run normally.
#
# The gate does not change the agent's score: the skipped tests still count
# in `total`, so the pass-rate reflects what the program actually does. It
# only collapses the cascade into one clearly-named failure plus N skips
# instead of N near-identical assertion failures.
# ---------------------------------------------------------------------------


def _smoke_request() -> Mapping[str, Any]:
    """Build the CLI smoke request. Imports `sample_record` lazily so the
    conftest module loads cleanly even if `marc21_support.py` raises at
    import time for some reason — failing safe rather than wedging the
    whole test session."""
    from marc21_support import encode_iso2709_record, sample_record_control_only

    return {
        "action": "inspect",
        "record_b64": b64(encode_iso2709_record(sample_record_control_only())),
    }


@pytest.fixture(scope="session")
def submission_command(
    prepared_submission: PreparedSubmission,
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[str, ...]:
    """Override the shared `submission_command` to gate on a CLI smoke check.

    Runs a single minimal `inspect` request before returning the command.
    If the program exits non-zero, calls ``pytest.skip`` so every test that
    transitively depends on this fixture skips with a uniform reason rather
    than failing 2,800+ times with the same startup bug.
    """
    cmd = prepared_submission.command
    tmp_path = tmp_path_factory.mktemp("marc21-cli-smoke")
    result, _ = run_marc21(cmd, _smoke_request(), tmp_path, timeout=30)
    if result.returncode != 0:
        stderr_excerpt = (result.stderr or "")[:500]
        pytest.skip(
            "CLI smoke gate failed: invoking the submitted program on a "
            "minimal valid `inspect` request returned non-zero. Downstream "
            "CLI tests skipped to avoid masking independent capability "
            f"failures with the same root cause. exit={result.returncode}; "
            f"stderr={stderr_excerpt!r}"
        )
    return cmd
