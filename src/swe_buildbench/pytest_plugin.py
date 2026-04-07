# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
"""Shared pytest fixtures for SWE-BuildBench eval test suites.

Each eval's ``conftest.py`` uses this module to avoid duplicating the
fixture boilerplate that resolves an implementation target, prepares a
build/runnable command, and exposes it to tests.

Usage inside an eval's ``conftest.py``::

    from swe_buildbench.pytest_plugin import (
        EvalConfig,
        pytest_addoption,  # noqa: F401 — re-export for pytest
        prepared_submission,  # noqa: F401
        repo_root,  # noqa: F401
        submission_command,  # noqa: F401
    )

    EVAL_CONFIG = EvalConfig(
        task_name="wordcount",
        default_reference_impl_subdir="Evals/WordCount/reference-implementation-cpp",
        python_reference_impl_subdir="Evals/WordCount/reference-implementation-python",
        env_var="SWEBUILDBENCH_WORDCOUNT_ROOT",
        preferred_executable_name="wordcount",
    )

Tests then request ``submission_command`` (a ``tuple[str, ...]`` that can
be splatted into ``subprocess.run``) or ``prepared_submission`` (the full
:class:`~swe_buildbench.build.PreparedSubmission`).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest

from swe_buildbench.build import (
    BuildBackend,
    CMakeBackend,
    JavaScriptBackend,
    LanguageTarget,
    PreparedSubmission,
    PythonBackend,
    find_repo_root,
)

SUPPORTED_LANGUAGES: tuple[str, ...] = ("cpp", "python", "javascript")


# ---------------------------------------------------------------------------
# Config object — each eval's conftest defines one EVAL_CONFIG module-level.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EvalConfig:
    """Per-eval configuration for the shared pytest fixtures."""

    task_name: str
    default_reference_impl_subdir: str
    env_var: str
    preferred_executable_name: str
    python_reference_impl_subdir: str | None = None
    javascript_reference_impl_subdir: str | None = None


def _load_eval_config(request: pytest.FixtureRequest) -> EvalConfig:
    """Locate the ``EVAL_CONFIG`` attribute on the eval's conftest module."""
    # Walk up the fixture's node chain to find a conftest exposing EVAL_CONFIG.
    for node in request.node.listchain():
        module = getattr(node, "module", None)
        if module is None:
            continue
        config = getattr(module, "EVAL_CONFIG", None)
        if isinstance(config, EvalConfig):
            return config

    # Fall back: scan all loaded conftests for one with EVAL_CONFIG.
    import sys

    for mod in sys.modules.values():
        config = getattr(mod, "EVAL_CONFIG", None)
        if isinstance(config, EvalConfig) and mod.__name__.endswith("conftest"):
            return config

    raise RuntimeError(
        "No EVAL_CONFIG found. Each eval's conftest.py must define "
        "EVAL_CONFIG = EvalConfig(...) at module level."
    )


# ---------------------------------------------------------------------------
# pytest options
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("swe-buildbench")
    group.addoption(
        "--implementation-root",
        action="store",
        default=None,
        help=(
            "Path to the implementation under test. Defaults to the eval's "
            "reference implementation for the selected --language."
        ),
    )
    group.addoption(
        "--language",
        action="store",
        default="cpp",
        choices=list(SUPPORTED_LANGUAGES),
        help="Target language for the implementation under test.",
    )
    group.addoption(
        "--build-timeout-seconds",
        action="store",
        default=300,
        type=int,
        help="Maximum seconds allowed for each build step.",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return find_repo_root(Path(__file__).resolve())


@pytest.fixture(scope="session")
def eval_language(request: pytest.FixtureRequest) -> str:
    return cast(str, request.config.getoption("--language"))


@pytest.fixture(scope="session")
def build_timeout_seconds(request: pytest.FixtureRequest) -> int:
    return cast(int, request.config.getoption("--build-timeout-seconds"))


@pytest.fixture(scope="session")
def language_target(
    request: pytest.FixtureRequest,
    repo_root: Path,
    eval_language: str,
) -> LanguageTarget:
    config = _load_eval_config(request)
    option_value = cast(str | None, request.config.getoption("--implementation-root"))

    if option_value:
        target = LanguageTarget(
            root=Path(option_value).expanduser().resolve(),
            language=eval_language,
            origin="pytest option --implementation-root",
            explicit=True,
        )
    elif config.env_var in os.environ:
        target = LanguageTarget(
            root=Path(os.environ[config.env_var]).expanduser().resolve(),
            language=eval_language,
            origin=f"environment variable {config.env_var}",
            explicit=True,
        )
    else:
        subdir = _default_reference_impl_subdir(config, eval_language)
        target = LanguageTarget(
            root=repo_root / subdir,
            language=eval_language,
            origin=f"default {eval_language} reference implementation",
            explicit=False,
        )

    missing = target.missing_requirements()
    if not missing:
        return target

    message = (
        f"The implementation target from {target.origin} is not buildable:\n"
        + "\n".join(f"- {entry}" for entry in missing)
        + f"\nProvide --implementation-root or set {config.env_var}."
    )
    if target.explicit:
        raise pytest.UsageError(message)
    pytest.skip(message)


def _default_reference_impl_subdir(config: EvalConfig, language: str) -> str:
    if language == "cpp":
        return config.default_reference_impl_subdir
    if language == "python":
        if config.python_reference_impl_subdir is None:
            raise pytest.UsageError(
                f"Task {config.task_name!r} has no Python reference implementation "
                "configured. Set python_reference_impl_subdir in EVAL_CONFIG."
            )
        return config.python_reference_impl_subdir
    if language == "javascript":
        if config.javascript_reference_impl_subdir is None:
            raise pytest.UsageError(
                f"Task {config.task_name!r} has no JavaScript reference implementation "
                "configured. Set javascript_reference_impl_subdir in EVAL_CONFIG."
            )
        return config.javascript_reference_impl_subdir
    raise pytest.UsageError(f"Unsupported language: {language}")


def _build_backend_for(language: str, config: EvalConfig) -> BuildBackend:
    if language == "cpp":
        return CMakeBackend(preferred_executable_name=config.preferred_executable_name)
    if language == "python":
        return PythonBackend()
    if language == "javascript":
        return JavaScriptBackend()
    raise pytest.UsageError(f"Unsupported language: {language}")


@pytest.fixture(scope="session")
def prepared_submission(
    request: pytest.FixtureRequest,
    language_target: LanguageTarget,
    build_timeout_seconds: int,
    tmp_path_factory: pytest.TempPathFactory,
) -> PreparedSubmission:
    config = _load_eval_config(request)
    backend = _build_backend_for(language_target.language, config)
    build_dir = tmp_path_factory.mktemp(f"{config.task_name}-build") / "build"
    return backend.prepare(
        language_target,
        build_dir=build_dir,
        timeout_seconds=build_timeout_seconds,
    )


@pytest.fixture(scope="session")
def submission_command(prepared_submission: PreparedSubmission) -> tuple[str, ...]:
    return prepared_submission.command
