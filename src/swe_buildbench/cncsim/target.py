from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Final

from swe_buildbench.build import ImplementationTarget

DEFAULT_IMPLEMENTATION_ENV_VAR: Final[str] = "SWEBUILDBENCH_IMPLEMENTATION_ROOT"


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
