"""Shared build and target resolution utilities (multi-language)."""

from .backends import (
    BuildBackend,
    CMakeBackend,
    LanguageTarget,
    PreparedSubmission,
    PythonBackend,
)
from .build import CMakeBuildResult, CommandExecutionError, CommandResult, build_cmake_project
from .target import ImplementationTarget, find_repo_root

__all__ = [
    "BuildBackend",
    "CMakeBackend",
    "CMakeBuildResult",
    "CommandExecutionError",
    "CommandResult",
    "ImplementationTarget",
    "LanguageTarget",
    "PreparedSubmission",
    "PythonBackend",
    "build_cmake_project",
    "find_repo_root",
]
