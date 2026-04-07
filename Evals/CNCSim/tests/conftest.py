from __future__ import annotations

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
    task_name="cncsim",
    default_reference_impl_subdir="Evals/CNCSim/reference-implementation-cpp",
    python_reference_impl_subdir="Evals/CNCSim/reference-implementation-python",
    env_var="SWEBUILDBENCH_IMPLEMENTATION_ROOT",
    preferred_executable_name="cncsim",
)
