from __future__ import annotations

import json
import subprocess
from base64 import b64decode, b64encode
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
