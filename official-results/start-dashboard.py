#!/usr/bin/env python
"""Launch the results dashboard web page.

This script starts a local Python HTTP server for `official-results/web` if one is
not already serving the dashboard, then opens the dashboard in the default browser.
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


DEFAULT_PORT = 8000
DEFAULT_DASHBOARD = "results-dashboard.html"
DASHBOARD_MARKER = "CNCSim XY Results Explorer"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start the official-results web dashboard and open it.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Port to serve on (default: %(default)s).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind the server to (default: %(default)s).",
    )
    parser.add_argument(
        "--dashboard",
        default=DEFAULT_DASHBOARD,
        help=f"Dashboard file to open (default: {DEFAULT_DASHBOARD}).",
    )
    parser.add_argument(
        "--max-ports",
        type=int,
        default=20,
        help="How many ports to probe for a free slot if the requested port is unavailable.",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Start the dashboard server only; do not open a browser tab.",
    )
    return parser.parse_args()


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.35)
        return sock.connect_ex((host, port)) == 0


def dashboard_url(base: str, dashboard: str) -> str:
    return f"{base.rstrip('/')}/{dashboard.lstrip('/')}"


def is_dashboard_running(base: str, dashboard: str) -> bool:
    try:
        with urllib.request.urlopen(dashboard_url(base, dashboard), timeout=1.0) as response:
            if response.status != 200:
                return False
            body = response.read(4096).decode("utf-8", errors="ignore")
            return DASHBOARD_MARKER in body
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def start_server(script_dir: Path, port: int, dashboard_dir: Path) -> subprocess.Popen:
    cmd = [
        sys.executable,
        "-m",
        "http.server",
        str(port),
        "--directory",
        str(dashboard_dir),
    ]
    kwargs = {"cwd": str(script_dir), "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if sys.platform.startswith("win"):
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["preexec_fn"] = os.setsid  # pragma: no cover

    return subprocess.Popen(cmd, **kwargs)


def wait_for_url(url: str, timeout_seconds: float = 3.0) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.4):
                return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.15)
    return False


def find_port(
    host: str,
    requested_port: int,
    dashboard: str,
    max_ports: int,
):
    for port in range(requested_port, requested_port + max_ports):
        base = f"http://{host}:{port}"
        if is_port_open(host, port):
            if is_dashboard_running(base, dashboard):
                return ("running", port)
            continue
        return ("free", port)
    return (None, None)


def main() -> None:
    args = parse_args()

    script_dir = Path(__file__).resolve().parent
    host = args.host
    requested_port = args.port
    dashboard = args.dashboard
    dashboard_dir = script_dir / "web"
    status, port = find_port(host, requested_port, dashboard, args.max_ports)

    if status is None:
        print(
            f"No free or matching server port found in range {requested_port}..{requested_port + args.max_ports - 1}.",
        )
        return

    base = f"http://{host}:{port}"
    url = dashboard_url(base, dashboard)

    if status == "running":
        print(f"Using existing dashboard server at {url}")
        if not args.no_open:
            webbrowser.open(url)
        return

    print(f"Starting dashboard server on {url} from {dashboard_dir}")
    try:
        start_server(script_dir, port, dashboard_dir)
    except OSError as exc:
        print(f"Failed to start server on port {port}: {exc}")
        return

    if not wait_for_url(url):
        print("Server started but did not become available quickly enough.")
        print(f"Attempting to open {url} anyway.")
    else:
        print(f"Server ready at {url}")

    if not args.no_open:
        webbrowser.open(url)


if __name__ == "__main__":
    main()
