from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from swe_buildbench.pytest_plugin import (
    EvalConfig,
    build_timeout_seconds,  # noqa: F401 — pytest fixture re-export
    eval_language,  # noqa: F401
    language_target,  # noqa: F401
    prepared_submission,  # noqa: F401
    pytest_addoption,  # noqa: F401
    repo_root,  # noqa: F401
    submission_command,  # noqa: F401
)

EVAL_CONFIG = EvalConfig(
    task_name="wordcount",
    default_reference_impl_subdir="Evals/WordCount/reference-implementation",
    python_reference_impl_subdir="Evals/WordCount/reference-implementation-python",
    env_var="SWEBUILDBENCH_WORDCOUNT_ROOT",
    preferred_executable_name="wordcount",
)


def run_wordcount(
    command: Sequence[str],
    input_text: str,
    tmp_path: Path,
    *,
    timeout: int = 30,
) -> dict[str, Any]:
    """Run the wordcount submission on the given input text, return parsed JSON."""
    input_file = tmp_path / "input.txt"
    output_file = tmp_path / "output.json"
    input_file.write_bytes(input_text.encode("utf-8"))

    result = subprocess.run(
        [*command, "--input", str(input_file), "--output", str(output_file)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    assert result.returncode == 0, (
        f"wordcount exited with code {result.returncode}\nstderr: {result.stderr}"
    )
    assert output_file.exists(), "Output file was not created"
    raw = output_file.read_text(encoding="utf-8")
    return cast(dict[str, Any], json.loads(raw))
