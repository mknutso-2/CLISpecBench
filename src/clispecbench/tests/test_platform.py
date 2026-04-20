"""Tests for platform detection utilities."""
# pyright: reportUnknownMemberType=false

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from clispecbench.harness.platform import resolve_host_home, wsl_path


class TestResolveHostHome:
    def test_linux_returns_home_directly(self) -> None:
        with (
            patch.object(sys, "platform", "linux"),
            patch.object(Path, "home", return_value=Path("/home/user")),
        ):
            result = resolve_host_home()
            assert result.as_posix() == "/home/user"

    def test_windows_converts_to_wsl_path(self) -> None:
        win_home = Path("C:\\Users\\TestUser")
        with (
            patch.object(sys, "platform", "win32"),
            patch.object(Path, "home", return_value=win_home),
        ):
            result = resolve_host_home()
            assert result.as_posix() == "/mnt/c/Users/TestUser"


class TestWslPath:
    def test_linux_passthrough(self) -> None:
        with patch.object(sys, "platform", "linux"):
            result = wsl_path(Path("/home/user/.claude"))
            assert str(result) == "/home/user/.claude"

    def test_windows_conversion(self) -> None:
        with patch.object(sys, "platform", "win32"):
            result = wsl_path(Path("C:\\Users\\Foo\\.claude"))
            assert str(result) == "/mnt/c/Users/Foo/.claude"
