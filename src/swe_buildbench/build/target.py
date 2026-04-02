from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ImplementationTarget:
    """A filesystem target that should contain a buildable CMake implementation."""

    root: Path
    origin: str
    explicit: bool

    @property
    def cmake_lists_path(self) -> Path:
        return self.root / "CMakeLists.txt"

    def missing_requirements(self) -> tuple[str, ...]:
        missing: list[str] = []

        if not self.root.exists():
            missing.append(f"missing directory: {self.root}")
        elif not self.root.is_dir():
            missing.append(f"not a directory: {self.root}")

        if not self.cmake_lists_path.is_file():
            missing.append(f"missing CMakeLists.txt: {self.cmake_lists_path}")

        return tuple(missing)


def find_repo_root(start: Path) -> Path:
    """Walk upward until the repository root containing `.git` is found."""

    anchor = start if start.is_dir() else start.parent
    for candidate in (anchor, *anchor.parents):
        if (candidate / ".git").exists():
            return candidate

    raise FileNotFoundError(f"Could not find repository root from {start}")
