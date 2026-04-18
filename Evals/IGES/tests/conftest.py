from __future__ import annotations

from swe_buildbench.pytest_plugin import (
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
    task_name="iges",
    reference_impl_subdirs={
        "cpp": "Evals/IGES/reference-implementation-cpp",
        "py": "Evals/IGES/reference-implementation-py",
        "js": "Evals/IGES/reference-implementation-js",
    },
    env_var="SWEBUILDBENCH_IGES_ROOT",
    preferred_executable_name="iges",
)
