"""Platform detection utilities for cross-platform Docker support."""

from __future__ import annotations

import sys
from pathlib import Path, PurePosixPath, PureWindowsPath


def resolve_host_home() -> Path:
    """Resolve the user's home directory for Docker volume mounts.

    On Linux, returns ``Path.home()`` directly.

    On Windows, the Docker daemon runs inside WSL2, so volume mount paths
    must use the WSL filesystem (``/mnt/c/Users/...``).  This function
    converts the Windows home path to its WSL equivalent.
    """
    home = Path.home()
    if sys.platform != "win32":
        return home

    # Convert C:\\Users\\Foo -> /mnt/c/Users/Foo
    win = PureWindowsPath(str(home))
    drive_letter = win.drive[0].lower()
    posix_path = win.relative_to(win.anchor).as_posix()
    return Path(f"/mnt/{drive_letter}/{posix_path}")


def wsl_path(win_path: Path) -> PurePosixPath:
    """Convert a Windows path to its WSL2 equivalent.

    Example: ``C:\\Users\\Foo\\.claude`` -> ``/mnt/c/Users/Foo/.claude``

    On non-Windows platforms, returns the path unchanged as a PurePosixPath.
    """
    if sys.platform != "win32":
        return PurePosixPath(win_path.as_posix())

    win = PureWindowsPath(str(win_path))
    drive_letter = win.drive[0].lower()
    posix_path = win.relative_to(win.anchor).as_posix()
    return PurePosixPath(f"/mnt/{drive_letter}/{posix_path}")
