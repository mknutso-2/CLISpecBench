from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

DEFAULT_IMPLEMENTATION_ENV_VAR: Final[str] = "SWEBUILDBENCH_IMPLEMENTATION_ROOT"


@dataclass(frozen=True, slots=True)
class ImplementationTarget:
    """A filesystem target that should contain a buildable CNCSim implementation."""

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


def default_reference_implementation_root(repo_root: Path) -> Path:
    """Return the default CNCSim reference implementation directory."""

    return repo_root / "CNCSim" / "reference-implementation"


def resolve_implementation_target(
    cli_value: str | None,
    *,
    env: Mapping[str, str],
    repo_root: Path,
) -> ImplementationTarget:
    """Resolve the implementation target from CLI, environment, or repo defaults."""

    if cli_value:
        return ImplementationTarget(
            root=_resolve_path(cli_value),
            origin="pytest option --implementation-root",
            explicit=True,
        )

    env_value = env.get(DEFAULT_IMPLEMENTATION_ENV_VAR)
    if env_value:
        return ImplementationTarget(
            root=_resolve_path(env_value),
            origin=f"environment variable {DEFAULT_IMPLEMENTATION_ENV_VAR}",
            explicit=True,
        )

    return ImplementationTarget(
        root=default_reference_implementation_root(repo_root),
        origin="default CNCSim reference implementation path",
        explicit=False,
    )


def _resolve_path(raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    return candidate.resolve()
