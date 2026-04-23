from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping, Sequence
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
    task_name="gedcom",
    reference_impl_subdirs={
        "py": "Evals/GEDCOM/reference-implementation-py",
    },
    env_var="CLISPECBENCH_GEDCOM_ROOT",
    preferred_executable_name="gedcom",
)


def run_gedcom(
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
