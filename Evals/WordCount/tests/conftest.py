from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
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

# Re-exported so pytest picks them up as fixtures/hooks in this conftest.
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
    task_name="wordcount",
    reference_impl_subdirs={
        "cpp": "Evals/WordCount/reference-implementation-cpp",
        "py": "Evals/WordCount/reference-implementation-py",
        "js": "Evals/WordCount/reference-implementation-js",
        "rs": "Evals/WordCount/reference-implementation-rs",
    },
    env_var="CLISPECBENCH_WORDCOUNT_ROOT",
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
    output_file.unlink(missing_ok=True)

    result = subprocess.run(
        [*command, "--input", str(input_file), "--output", str(output_file)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    # Exit-code conformance has a dedicated gate. Observable counts still carry
    # useful signal when a submission writes correct JSON but exits incorrectly.
    assert output_file.exists(), (
        f"Output file was not created; exit={result.returncode}; stderr={result.stderr}"
    )
    raw = output_file.read_text(encoding="utf-8")
    return cast(dict[str, Any], json.loads(raw))
