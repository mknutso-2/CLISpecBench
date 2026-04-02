from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import pytest

from swe_buildbench.build import (
    CMakeBuildResult,
    ImplementationTarget,
    build_cmake_project,
    find_repo_root,
)

WORDCOUNT_IMPLEMENTATION_ENV_VAR = "SWEBUILDBENCH_WORDCOUNT_ROOT"


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("wordcount")
    group.addoption(
        "--implementation-root",
        action="store",
        default=None,
        help=(
            "Path to the CMake-based implementation under test. Defaults to "
            "WordCount/reference-implementation or SWEBUILDBENCH_WORDCOUNT_ROOT."
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

    if option_value:
        target = ImplementationTarget(
            root=Path(option_value).resolve(),
            origin="pytest option --implementation-root",
            explicit=True,
        )
    elif WORDCOUNT_IMPLEMENTATION_ENV_VAR in os.environ:
        target = ImplementationTarget(
            root=Path(os.environ[WORDCOUNT_IMPLEMENTATION_ENV_VAR]).resolve(),
            origin=f"environment variable {WORDCOUNT_IMPLEMENTATION_ENV_VAR}",
            explicit=True,
        )
    else:
        target = ImplementationTarget(
            root=repo_root / "Evals" / "WordCount" / "reference-implementation",
            origin="default WordCount reference implementation path",
            explicit=False,
        )

    missing = target.missing_requirements()
    if not missing:
        return target

    message = (
        f"The implementation target from {target.origin} is not buildable:\n"
        + "\n".join(f"- {entry}" for entry in missing)
        + (
            f"\nProvide --implementation-root or set {WORDCOUNT_IMPLEMENTATION_ENV_VAR} "
            "to a CMake project directory."
        )
    )
    if target.explicit:
        raise pytest.UsageError(message)
    pytest.skip(message)


@pytest.fixture(scope="session")
def build_result(
    implementation_target: ImplementationTarget,
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> CMakeBuildResult:
    timeout = cast(int, request.config.getoption("--build-timeout-seconds"))
    build_dir = tmp_path_factory.mktemp("wordcount-build") / "build"
    return build_cmake_project(
        implementation_target,
        build_dir=build_dir,
        timeout_seconds=timeout,
    )


@pytest.fixture(scope="session")
def built_executable_path(build_result: CMakeBuildResult) -> Path:
    candidates = [
        path
        for path in build_result.build_dir.rglob("*")
        if _is_executable_candidate(path, build_result.build_dir)
    ]
    if not candidates:
        raise AssertionError(
            f"Could not find a built executable under {build_result.build_dir}"
        )
    return min(candidates, key=lambda p: _executable_sort_key(p, build_result.build_dir))


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


def _executable_sort_key(path: Path, build_dir: Path) -> tuple[int, int, float, str]:
    relative_path = path.relative_to(build_dir)
    return (
        0 if "wordcount" in path.name.lower() else 1,
        len(relative_path.parts),
        -path.stat().st_mtime,
        str(relative_path),
    )


def run_wordcount(
    executable: Path,
    input_text: str,
    tmp_path: Path,
    *,
    timeout: int = 30,
) -> dict[str, Any]:
    """Run the wordcount executable on the given input text, return parsed JSON."""
    input_file = tmp_path / "input.txt"
    output_file = tmp_path / "output.json"
    input_file.write_bytes(input_text.encode("utf-8"))

    result = subprocess.run(
        [str(executable), "--input", str(input_file), "--output", str(output_file)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    assert result.returncode == 0, (
        f"wordcount exited with code {result.returncode}\n"
        f"stderr: {result.stderr}"
    )
    assert output_file.exists(), "Output file was not created"
    raw = output_file.read_text(encoding="utf-8")
    return cast(dict[str, Any], json.loads(raw))
