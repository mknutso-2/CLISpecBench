from __future__ import annotations

import os
from pathlib import Path
from typing import cast

import pytest

from swe_buildbench.cncsim import (
    DEFAULT_IMPLEMENTATION_ENV_VAR,
    CMakeBuildResult,
    ImplementationTarget,
    build_cmake_project,
    find_repo_root,
    resolve_implementation_target,
)


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("cncsim")
    group.addoption(
        "--implementation-root",
        action="store",
        default=None,
        help=(
            "Path to the CMake-based implementation under test. Defaults to "
            "CNCSim/reference-implementation or SWEBUILDBENCH_IMPLEMENTATION_ROOT."
        ),
    )
    group.addoption(
        "--build-timeout-seconds",
        action="store",
        default=300,
        type=int,
        help="Maximum seconds allowed for each CMake configure/build step.",
    )


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return find_repo_root(Path(__file__).resolve())


@pytest.fixture(scope="session")
def implementation_target(request: pytest.FixtureRequest, repo_root: Path) -> ImplementationTarget:
    option_value = cast(str | None, request.config.getoption("--implementation-root"))
    target = resolve_implementation_target(option_value, env=os.environ, repo_root=repo_root)

    missing_requirements = target.missing_requirements()
    if not missing_requirements:
        return target

    message = (
        f"The implementation target from {target.origin} is not buildable:\n"
        + "\n".join(f"- {entry}" for entry in missing_requirements)
        + (
            f"\nProvide --implementation-root or set {DEFAULT_IMPLEMENTATION_ENV_VAR} "
            "to a CMake project directory."
        )
    )
    if target.explicit:
        raise pytest.UsageError(message)

    pytest.skip(message)


@pytest.fixture(scope="session")
def build_timeout_seconds(request: pytest.FixtureRequest) -> int:
    return cast(int, request.config.getoption("--build-timeout-seconds"))


@pytest.fixture(scope="session")
def build_result(
    implementation_target: ImplementationTarget,
    build_timeout_seconds: int,
    tmp_path_factory: pytest.TempPathFactory,
) -> CMakeBuildResult:
    build_dir = tmp_path_factory.mktemp("cncsim-build") / "build"
    return build_cmake_project(
        implementation_target,
        build_dir=build_dir,
        timeout_seconds=build_timeout_seconds,
    )
