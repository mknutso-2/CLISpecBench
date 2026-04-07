"""Build backend abstraction for multi-language eval targets.

A :class:`BuildBackend` turns a :class:`LanguageTarget` (a directory containing
an implementation) into a :class:`PreparedSubmission` whose ``command`` is the
argv that invokes the built/runnable program.
"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Protocol, runtime_checkable

from .build import CMakeBuildResult, build_cmake_project
from .target import ImplementationTarget

DEFAULT_BUILD_TIMEOUT_SECONDS: Final[int] = 300


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LanguageTarget:
    """A filesystem directory containing an implementation in a given language."""

    root: Path
    language: str
    origin: str
    explicit: bool

    def missing_requirements(self) -> tuple[str, ...]:
        missing: list[str] = []

        if not self.root.exists():
            missing.append(f"missing directory: {self.root}")
            return tuple(missing)
        if not self.root.is_dir():
            missing.append(f"not a directory: {self.root}")
            return tuple(missing)

        if self.language == "cpp":
            cmake_lists = self.root / "CMakeLists.txt"
            if not cmake_lists.is_file():
                missing.append(f"missing CMakeLists.txt: {cmake_lists}")
        elif self.language == "python":
            main_py = self.root / "main.py"
            if not main_py.is_file():
                missing.append(f"missing main.py: {main_py}")
        elif self.language == "javascript":
            main_js = self.root / "main.js"
            if not main_js.is_file():
                missing.append(f"missing main.js: {main_js}")
        else:
            missing.append(f"unknown language: {self.language}")

        return tuple(missing)

    def to_implementation_target(self) -> ImplementationTarget:
        """Legacy adapter: callers that still expect ``ImplementationTarget``."""
        return ImplementationTarget(
            root=self.root,
            origin=self.origin,
            explicit=self.explicit,
        )


@dataclass(frozen=True, slots=True)
class PreparedSubmission:
    """A buildable/runnable submission ready to be invoked by test helpers."""

    command: tuple[str, ...]
    build_dir: Path
    language: str
    build_result: CMakeBuildResult | None = field(default=None)


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class BuildBackend(Protocol):
    """Prepares a submission so test helpers can invoke it as a subprocess."""

    def prepare(
        self,
        target: LanguageTarget,
        *,
        build_dir: Path,
        timeout_seconds: int = DEFAULT_BUILD_TIMEOUT_SECONDS,
    ) -> PreparedSubmission: ...


# ---------------------------------------------------------------------------
# PythonBackend
# ---------------------------------------------------------------------------


class PythonBackend:
    """Runs a Python submission via ``python3 main.py`` with no build step."""

    def __init__(self, entry_point: str = "main.py") -> None:
        self._entry_point = entry_point

    def prepare(
        self,
        target: LanguageTarget,
        *,
        build_dir: Path,
        timeout_seconds: int = DEFAULT_BUILD_TIMEOUT_SECONDS,
    ) -> PreparedSubmission:
        del timeout_seconds  # no build step, nothing to time out

        entry = target.root / self._entry_point
        if not entry.is_file():
            raise FileNotFoundError(f"Python backend requires {self._entry_point} at {entry}")

        build_dir.mkdir(parents=True, exist_ok=True)
        interpreter = _resolve_python_interpreter()
        return PreparedSubmission(
            command=(interpreter, str(entry)),
            build_dir=build_dir,
            language="python",
        )


# ---------------------------------------------------------------------------
# JavaScriptBackend
# ---------------------------------------------------------------------------


class JavaScriptBackend:
    """Runs a JavaScript submission via ``node main.js`` with no build step."""

    def __init__(self, entry_point: str = "main.js") -> None:
        self._entry_point = entry_point

    def prepare(
        self,
        target: LanguageTarget,
        *,
        build_dir: Path,
        timeout_seconds: int = DEFAULT_BUILD_TIMEOUT_SECONDS,
    ) -> PreparedSubmission:
        del timeout_seconds  # no build step, nothing to time out

        entry = target.root / self._entry_point
        if not entry.is_file():
            raise FileNotFoundError(
                f"JavaScript backend requires {self._entry_point} at {entry}"
            )

        build_dir.mkdir(parents=True, exist_ok=True)
        node = _resolve_node_interpreter()
        return PreparedSubmission(
            command=(node, str(entry)),
            build_dir=build_dir,
            language="javascript",
        )


def _resolve_node_interpreter() -> str:
    """Return a Node.js interpreter path. Errors clearly if missing."""
    node = shutil.which("node")
    if node is not None:
        return node
    raise FileNotFoundError(
        "JavaScript backend requires Node.js: 'node' was not found on PATH"
    )


def _resolve_python_interpreter() -> str:
    """Return a python interpreter path. Prefers ``python3`` on POSIX."""
    if sys.platform != "win32":
        python3 = shutil.which("python3")
        if python3 is not None:
            return python3
    python = shutil.which("python")
    if python is not None:
        return python
    # Fall back to the interpreter currently running pytest.
    return sys.executable


# ---------------------------------------------------------------------------
# CMakeBackend
# ---------------------------------------------------------------------------


class CMakeBackend:
    """Builds a CMake project and discovers its main executable."""

    def __init__(self, *, preferred_executable_name: str | None = None) -> None:
        self._preferred_name = preferred_executable_name

    def prepare(
        self,
        target: LanguageTarget,
        *,
        build_dir: Path,
        timeout_seconds: int = DEFAULT_BUILD_TIMEOUT_SECONDS,
    ) -> PreparedSubmission:
        build_result = build_cmake_project(
            target.to_implementation_target(),
            build_dir=build_dir,
            timeout_seconds=timeout_seconds,
        )
        executable = self._discover_executable(build_result.build_dir)
        return PreparedSubmission(
            command=(str(executable),),
            build_dir=build_result.build_dir,
            language="cpp",
            build_result=build_result,
        )

    def _discover_executable(self, build_dir: Path) -> Path:
        candidates = [
            path for path in build_dir.rglob("*") if _is_executable_candidate(path, build_dir)
        ]
        if not candidates:
            raise AssertionError(f"Could not find a built executable under {build_dir}")
        return min(
            candidates,
            key=lambda path: _executable_sort_key(path, build_dir, self._preferred_name),
        )


def _is_executable_candidate(path: Path, build_dir: Path) -> bool:
    if not path.is_file():
        return False

    relative_parts = {part.lower() for part in path.relative_to(build_dir).parts}
    if {"cmakefiles", "testing", "_deps"} & relative_parts:
        return False

    lower_name = path.name.lower()
    if lower_name.startswith(("cmtc_", "compilerid")):
        return False

    if sys.platform == "win32":
        return path.suffix.lower() == ".exe"

    if not os.access(path, os.X_OK):
        return False

    return path.suffix.lower() not in {".a", ".dylib", ".o", ".obj", ".so"}


def _executable_sort_key(
    path: Path,
    build_dir: Path,
    preferred_name: str | None,
) -> tuple[int, int, float, str]:
    relative_path = path.relative_to(build_dir)
    name_priority = 1
    if preferred_name is not None and preferred_name.lower() in path.name.lower():
        name_priority = 0
    return (
        name_priority,
        len(relative_path.parts),
        -path.stat().st_mtime,
        str(relative_path),
    )
