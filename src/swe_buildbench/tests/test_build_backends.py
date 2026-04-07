"""Tests for the BuildBackend abstraction (Python + CMake backends)."""
# pyright: reportUnknownMemberType=false

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from swe_buildbench.build import (
    BuildBackend,
    CMakeBackend,
    JavaScriptBackend,
    LanguageTarget,
    PreparedSubmission,
    PythonBackend,
    RustBackend,
)

_HAS_CARGO = shutil.which("cargo") is not None

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# PythonBackend
# ---------------------------------------------------------------------------


class TestPythonBackend:
    def test_prepare_returns_command_pointing_at_main_py(self, tmp_path: Path) -> None:
        main_py = tmp_path / "main.py"
        main_py.write_text("print('hi')\n", encoding="utf-8")

        target = LanguageTarget(
            root=tmp_path,
            language="py",
            origin="test",
            explicit=True,
        )
        backend = PythonBackend()

        prepared = backend.prepare(target, build_dir=tmp_path / "build")

        assert isinstance(prepared, PreparedSubmission)
        interpreter_name = Path(prepared.command[0]).stem.lower()
        assert interpreter_name in ("python", "python3")
        assert Path(prepared.command[-1]).resolve() == main_py.resolve()

    def test_prepared_command_actually_runs(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("import sys; sys.stdout.write('ok')\n", encoding="utf-8")
        target = LanguageTarget(
            root=tmp_path,
            language="py",
            origin="test",
            explicit=True,
        )
        backend = PythonBackend()

        prepared = backend.prepare(target, build_dir=tmp_path / "build")
        result = subprocess.run(
            list(prepared.command),
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert result.stdout == "ok"

    def test_prepare_raises_when_main_py_missing(self, tmp_path: Path) -> None:
        target = LanguageTarget(
            root=tmp_path,
            language="py",
            origin="test",
            explicit=True,
        )
        backend = PythonBackend()

        with pytest.raises(FileNotFoundError, match="main.py"):
            backend.prepare(target, build_dir=tmp_path / "build")


# ---------------------------------------------------------------------------
# JavaScriptBackend
# ---------------------------------------------------------------------------


class TestJavaScriptBackend:
    def test_prepare_returns_command_pointing_at_main_js(self, tmp_path: Path) -> None:
        main_js = tmp_path / "main.js"
        main_js.write_text("console.log('hi');\n", encoding="utf-8")

        target = LanguageTarget(
            root=tmp_path,
            language="js",
            origin="test",
            explicit=True,
        )
        backend = JavaScriptBackend()

        prepared = backend.prepare(target, build_dir=tmp_path / "build")

        assert isinstance(prepared, PreparedSubmission)
        assert prepared.language == "js"
        assert Path(prepared.command[0]).stem.lower() == "node"
        assert Path(prepared.command[-1]).resolve() == main_js.resolve()

    def test_prepared_command_actually_runs(self, tmp_path: Path) -> None:
        (tmp_path / "main.js").write_text("process.stdout.write('ok');\n", encoding="utf-8")
        target = LanguageTarget(
            root=tmp_path,
            language="js",
            origin="test",
            explicit=True,
        )
        backend = JavaScriptBackend()

        prepared = backend.prepare(target, build_dir=tmp_path / "build")
        result = subprocess.run(
            list(prepared.command),
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert result.stdout == "ok"

    def test_prepare_raises_when_main_js_missing(self, tmp_path: Path) -> None:
        target = LanguageTarget(
            root=tmp_path,
            language="js",
            origin="test",
            explicit=True,
        )
        backend = JavaScriptBackend()

        with pytest.raises(FileNotFoundError, match="main.js"):
            backend.prepare(target, build_dir=tmp_path / "build")


# ---------------------------------------------------------------------------
# RustBackend
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _HAS_CARGO, reason="cargo not installed on this host")
class TestRustBackend:
    def test_prepare_returns_cargo_run_command(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.rs").write_text('fn main() { print!("ok"); }\n', encoding="utf-8")
        (tmp_path / "Cargo.toml").write_text(
            '[package]\nname = "smoke"\nversion = "0.1.0"\nedition = "2021"\n'
            '[[bin]]\nname = "smoke"\npath = "src/main.rs"\n[dependencies]\n',
            encoding="utf-8",
        )
        target = LanguageTarget(
            root=tmp_path,
            language="rs",
            origin="test",
            explicit=True,
        )
        backend = RustBackend()

        prepared = backend.prepare(target, build_dir=tmp_path / "build")

        assert isinstance(prepared, PreparedSubmission)
        assert prepared.language == "rs"
        assert "cargo" in Path(prepared.command[0]).stem.lower()
        assert "run" in prepared.command
        assert prepared.command[-1] == "--"

    def test_prepared_command_actually_runs(self, tmp_path: Path) -> None:
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.rs").write_text(
            'use std::io::Write; fn main() { std::io::stdout().write_all(b"ok").unwrap(); }\n',
            encoding="utf-8",
        )
        (tmp_path / "Cargo.toml").write_text(
            '[package]\nname = "smoke"\nversion = "0.1.0"\nedition = "2021"\n'
            '[[bin]]\nname = "smoke"\npath = "src/main.rs"\n[dependencies]\n',
            encoding="utf-8",
        )
        target = LanguageTarget(
            root=tmp_path,
            language="rs",
            origin="test",
            explicit=True,
        )
        backend = RustBackend()

        prepared = backend.prepare(target, build_dir=tmp_path / "build")
        result = subprocess.run(
            list(prepared.command),
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert result.returncode == 0
        assert result.stdout == "ok"

    def test_prepare_raises_when_cargo_toml_missing(self, tmp_path: Path) -> None:
        target = LanguageTarget(
            root=tmp_path,
            language="rs",
            origin="test",
            explicit=True,
        )
        backend = RustBackend()

        with pytest.raises(FileNotFoundError, match="Cargo.toml"):
            backend.prepare(target, build_dir=tmp_path / "build")


# ---------------------------------------------------------------------------
# CMakeBackend (wraps existing build_cmake_project + executable discovery)
# ---------------------------------------------------------------------------


class TestCMakeBackend:
    def test_prepare_returns_runnable_executable(self, tmp_path: Path) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        reference_impl = repo_root / "Evals" / "WordCount" / "reference-implementation-cpp"
        if not (reference_impl / "CMakeLists.txt").is_file():
            pytest.skip("WordCount reference implementation not available")

        target = LanguageTarget(
            root=reference_impl,
            language="cpp",
            origin="test",
            explicit=True,
        )
        backend = CMakeBackend(preferred_executable_name="wordcount")

        prepared = backend.prepare(target, build_dir=tmp_path / "build")

        assert len(prepared.command) == 1
        assert Path(prepared.command[0]).is_file()

        # Smoke test: running with no args should exit 1 per the WordCount spec
        result = subprocess.run(
            list(prepared.command),
            capture_output=True,
            timeout=10,
        )
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestBuildBackendProtocol:
    def test_python_backend_satisfies_protocol(self) -> None:
        assert isinstance(PythonBackend(), BuildBackend)

    def test_cmake_backend_satisfies_protocol(self) -> None:
        assert isinstance(CMakeBackend(), BuildBackend)

    def test_rust_backend_satisfies_protocol(self) -> None:
        assert isinstance(RustBackend(), BuildBackend)
