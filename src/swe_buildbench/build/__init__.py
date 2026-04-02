"""Shared CMake build and target resolution utilities."""

from .build import CMakeBuildResult, CommandExecutionError, CommandResult, build_cmake_project
from .target import ImplementationTarget, find_repo_root

__all__ = [
    "CMakeBuildResult",
    "CommandExecutionError",
    "CommandResult",
    "ImplementationTarget",
    "build_cmake_project",
    "find_repo_root",
]
