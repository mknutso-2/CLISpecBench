"""CNCSim-specific test harness utilities."""

from .build import CMakeBuildResult, CommandExecutionError, CommandResult, build_cmake_project
from .target import (
    DEFAULT_IMPLEMENTATION_ENV_VAR,
    ImplementationTarget,
    default_reference_implementation_root,
    find_repo_root,
    resolve_implementation_target,
)

__all__ = [
    "CMakeBuildResult",
    "CommandExecutionError",
    "CommandResult",
    "DEFAULT_IMPLEMENTATION_ENV_VAR",
    "ImplementationTarget",
    "build_cmake_project",
    "default_reference_implementation_root",
    "find_repo_root",
    "resolve_implementation_target",
]
