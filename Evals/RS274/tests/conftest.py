from __future__ import annotations

import pytest

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


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "trace: tests for the v2.0.0 motion trace feature")


EVAL_CONFIG = EvalConfig(
    task_name="rs274",
    reference_impl_subdirs={
        "cpp": "Evals/RS274/reference-implementation-cpp",
        "py": "Evals/RS274/reference-implementation-py",
        "js": "Evals/RS274/reference-implementation-js",
        "rs": "Evals/RS274/reference-implementation-rs",
    },
    env_var="CLISPECBENCH_RS274_ROOT",
    preferred_executable_name="rs274",
)
