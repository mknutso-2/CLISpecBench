from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from .target import ImplementationTarget

DEFAULT_BUILD_TIMEOUT_SECONDS: Final[int] = 300


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Captured output for a completed process invocation."""

    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class CommandExecutionError(RuntimeError):
    """Raised when a build command fails or times out."""

    def __init__(self, step_name: str, result: CommandResult, timeout_seconds: int | None) -> None:
        timeout_suffix = "" if timeout_seconds is None else f" after {timeout_seconds} seconds"
        message = (
            f"{step_name} failed{timeout_suffix}.\n"
            f"Command: {' '.join(result.args)}\n"
            f"Return code: {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        super().__init__(message)
        self.step_name = step_name
        self.result = result
        self.timeout_seconds = timeout_seconds


@dataclass(frozen=True, slots=True)
class CMakeBuildResult:
    """The full result of configuring and building a CMake project."""

    target: ImplementationTarget
    build_dir: Path
    configure: CommandResult
    build: CommandResult


def build_cmake_project(
    target: ImplementationTarget,
    *,
    build_dir: Path,
    timeout_seconds: int = DEFAULT_BUILD_TIMEOUT_SECONDS,
) -> CMakeBuildResult:
    """Configure and build a CMake project rooted at `target.root`."""

    build_dir.mkdir(parents=True, exist_ok=True)

    configure = _run_command(
        "cmake configure",
        ("cmake", "-S", str(target.root), "-B", str(build_dir)),
        cwd=target.root,
        timeout_seconds=timeout_seconds,
    )
    build = _run_command(
        "cmake build",
        ("cmake", "--build", str(build_dir), "--parallel"),
        cwd=target.root,
        timeout_seconds=timeout_seconds,
    )

    return CMakeBuildResult(
        target=target,
        build_dir=build_dir,
        configure=configure,
        build=build,
    )


def _run_command(
    step_name: str,
    args: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: int,
) -> CommandResult:
    try:
        completed = subprocess.run(
            list(args),
            capture_output=True,
            check=False,
            cwd=cwd,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        result = CommandResult(
            args=tuple(str(arg) for arg in args),
            returncode=-1,
            stdout=_coerce_output(error.stdout),
            stderr=_coerce_output(error.stderr),
        )
        raise CommandExecutionError(step_name, result, timeout_seconds) from error

    result = CommandResult(
        args=tuple(str(arg) for arg in args),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
    if completed.returncode != 0:
        raise CommandExecutionError(step_name, result, None)

    return result


def _coerce_output(stream: str | bytes | None) -> str:
    if stream is None:
        return ""
    if isinstance(stream, bytes):
        return stream.decode("utf-8", errors="replace")
    return stream
