"""Smoke tests that run inside real Docker containers.

These tests verify that the agent container environments are functional —
tools like Bash, cmake, and g++ work correctly.  They require Docker to be
running and the base image to be built.

Marked with ``pytest.mark.docker`` so they can be selected or skipped:

    pytest -m docker          # run only Docker smoke tests
    pytest -m "not docker"    # skip them
"""

from __future__ import annotations

from pathlib import Path

import pytest

from swe_buildbench.harness.docker import ContainerConfig, DockerSandbox

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AGENT_IMAGE = "swe-buildbench-claude-code"
BASE_IMAGE = "swe-buildbench-base"


def _image_available(tag: str) -> bool:
    try:
        sandbox = DockerSandbox()
        return sandbox.image_exists(tag)
    except Exception:
        return False


def _run_in_container(
    image: str,
    command: str,
    *,
    user: str | None = None,
    environment: dict[str, str] | None = None,
    timeout: float = 30,
) -> tuple[int | None, str]:
    """Run a one-shot command in a container and return (exit_code, logs)."""
    if user:
        # Use base64 encoding to avoid shell quoting issues with su -c
        import base64
        encoded = base64.b64encode(command.encode()).decode()
        cmd = ["bash", "-c", f"echo {encoded} | base64 -d | su {user} -s /bin/bash"]
    else:
        cmd = ["bash", "-c", command]
    config = ContainerConfig(
        image=image,
        environment=environment or {},
        command=cmd,
        network_mode="none",
    )
    sandbox = DockerSandbox()
    return sandbox.run_oneshot(config, timeout)


docker = pytest.mark.docker
skip_no_agent_image = pytest.mark.skipif(
    not _image_available(AGENT_IMAGE),
    reason=f"Docker image {AGENT_IMAGE} not available",
)
skip_no_base_image = pytest.mark.skipif(
    not _image_available(BASE_IMAGE),
    reason=f"Docker image {BASE_IMAGE} not available",
)


# ---------------------------------------------------------------------------
# Claude Code agent container — Bash tool functionality
# ---------------------------------------------------------------------------


@docker
@skip_no_agent_image
class TestClaudeCodeBashTool:
    """Verify that the 'agent' user can run shell commands.

    The Bash tool in Claude Code creates a session-env directory under
    ~/.claude/.  If ~/.claude is mounted read-only (for credential pass-
    through), Bash tool invocations fail with ENOENT.

    These tests catch that regression by running commands as the 'agent'
    user, exactly as the runner does via ``su agent -c '...'``.
    """

    def test_agent_can_run_basic_commands(self) -> None:
        """The agent user can execute simple shell commands."""
        exit_code, logs = _run_in_container(
            AGENT_IMAGE, "echo hello && whoami", user="agent",
        )
        assert exit_code == 0, f"Basic command failed: {logs}"
        assert "hello" in logs

    def test_agent_can_mkdir_in_home(self) -> None:
        """The agent user can create directories under $HOME.

        Claude Code's Bash tool needs to create ~/.claude/session-env/.
        """
        exit_code, logs = _run_in_container(
            AGENT_IMAGE,
            "mkdir -p /home/agent/.claude/session-env/test-session && echo ok",
            user="agent",
        )
        assert exit_code == 0, f"mkdir in ~/.claude failed: {logs}"
        assert "ok" in logs

    def test_agent_can_write_session_env_with_credential_file_mounts(self) -> None:
        """Claude Code can create session-env when credential files are ro-mounted.

        The runner mounts individual credential files (not the whole dir) into
        /home/agent/.claude/ as read-only.  This leaves the directory itself
        writable so Claude Code's Bash tool can create session-env/ at runtime.

        Previously, the entire ~/.claude dir was mounted ro, which caused every
        Bash tool invocation to fail with ENOENT / "Read-only file system".
        """
        import tempfile

        from swe_buildbench.harness.platform import wsl_path

        with tempfile.TemporaryDirectory(prefix="claude-cred-") as cred_dir:
            cred_file = Path(cred_dir) / ".credentials.json"
            cred_file.write_text("{}")

            mount_src = str(wsl_path(cred_file))

            config = ContainerConfig(
                image=AGENT_IMAGE,
                environment={},
                command=[
                    "bash", "-c",
                    # Ensure the .claude dir exists and is owned by agent,
                    # then verify both: credential is readable and session-env
                    # can be created.
                    "mkdir -p /home/agent/.claude"
                    " && chown agent:agent /home/agent/.claude"
                    " && su agent -c '"
                    "cat /home/agent/.claude/.credentials.json > /dev/null"
                    " && mkdir -p /home/agent/.claude/session-env/test"
                    " && echo ok'",
                ],
                volumes={
                    mount_src: {
                        "bind": "/home/agent/.claude/.credentials.json",
                        "mode": "ro",
                    },
                },
                network_mode="none",
            )
            sandbox = DockerSandbox()
            exit_code, logs = sandbox.run_oneshot(config, timeout_seconds=15)

        assert exit_code == 0, (
            f"session-env creation failed with credential file mount "
            f"(exit={exit_code}): {logs}"
        )

    def test_agent_can_run_cmake(self) -> None:
        """cmake is available to the agent user."""
        exit_code, logs = _run_in_container(
            AGENT_IMAGE, "cmake --version", user="agent",
        )
        assert exit_code == 0, f"cmake not available: {logs}"
        assert "cmake version" in logs

    def test_agent_can_run_gpp(self) -> None:
        """g++ is available to the agent user."""
        exit_code, logs = _run_in_container(
            AGENT_IMAGE, "g++-14 --version", user="agent",
        )
        assert exit_code == 0, f"g++ not available: {logs}"
        assert "g++" in logs.lower()

    def test_agent_can_compile_and_run_cpp(self) -> None:
        """The agent user can compile and execute a C++ program."""
        import tempfile

        from pathlib import PurePosixPath

        with tempfile.TemporaryDirectory(prefix="cpp-test-") as td:
            src = Path(td) / "test.cpp"
            src.write_text(
                '#include <iostream>\n'
                'int main() { std::cout << "compiled ok" << std::endl; }\n'
            )

            config = ContainerConfig(
                image=AGENT_IMAGE,
                environment={},
                command=["bash", "-c", (
                    "chown agent:agent /tmp/test.cpp"
                    " && su agent -c '"
                    "g++-14 -std=c++20 -o /tmp/test /tmp/test.cpp && /tmp/test"
                    "'"
                )],
                network_mode="none",
            )
            sandbox = DockerSandbox()
            try:
                sandbox.create(config)
                sandbox.copy_in(src, PurePosixPath("/tmp/test.cpp"))
                run = sandbox.start_and_wait(30)
                logs = sandbox.get_logs()
            finally:
                sandbox.cleanup()

        assert run.exit_code == 0, f"C++ compile+run failed: {logs}"
        assert "compiled ok" in logs


# ---------------------------------------------------------------------------
# Base image — build toolchain
# ---------------------------------------------------------------------------


@docker
@skip_no_base_image
class TestBaseImageToolchain:
    """Verify that the base image has the expected build tools."""

    def test_cmake_available(self) -> None:
        exit_code, logs = _run_in_container(BASE_IMAGE, "cmake --version")
        assert exit_code == 0, f"cmake not found: {logs}"

    def test_gpp_available(self) -> None:
        exit_code, logs = _run_in_container(BASE_IMAGE, "g++-14 --version")
        assert exit_code == 0, f"g++-14 not found: {logs}"

    def test_python3_available(self) -> None:
        exit_code, logs = _run_in_container(BASE_IMAGE, "python3 --version")
        assert exit_code == 0, f"python3 not found: {logs}"

    def test_pytest_available(self) -> None:
        exit_code, logs = _run_in_container(BASE_IMAGE, "python3 -m pytest --version")
        assert exit_code == 0, f"pytest not found: {logs}"

    def test_node_available(self) -> None:
        exit_code, logs = _run_in_container(BASE_IMAGE, "node --version")
        assert exit_code == 0, f"node not found: {logs}"

    def test_cmake_build_roundtrip(self) -> None:
        """A minimal cmake project can configure, build, and run."""
        from pathlib import PurePosixPath

        sandbox = DockerSandbox()
        config = ContainerConfig(
            image=BASE_IMAGE,
            environment={},
            command=["bash", "-c", (
                "cd /tmp/proj/build"
                " && cmake .. -DCMAKE_BUILD_TYPE=Release 2>&1"
                " && cmake --build . 2>&1"
                " && ./smoke"
            )],
            network_mode="none",
        )

        import tempfile

        with tempfile.TemporaryDirectory(prefix="smoke-proj-") as proj_dir:
            proj = Path(proj_dir)
            (proj / "src").mkdir()
            (proj / "build").mkdir()
            (proj / "CMakeLists.txt").write_text(
                "cmake_minimum_required(VERSION 3.20)\n"
                "project(smoke CXX)\n"
                "set(CMAKE_CXX_STANDARD 20)\n"
                "add_executable(smoke src/main.cpp)\n"
            )
            (proj / "src" / "main.cpp").write_text(
                "#include <iostream>\n"
                "#include <algorithm>\n"
                "#include <vector>\n"
                "int main() {\n"
                "  std::vector<int> v{3,1,2};\n"
                "  std::sort(v.begin(),v.end());\n"
                "  std::cout << v[0] << v[1] << v[2] << std::endl;\n"
                "  return 0;\n"
                "}\n"
            )

            try:
                sandbox.create(config)
                sandbox.copy_in(proj, PurePosixPath("/tmp/proj"))
                run = sandbox.start_and_wait(60)
                logs = sandbox.get_logs()
            finally:
                sandbox.cleanup()

        assert run.exit_code == 0, f"cmake roundtrip failed: {logs}"
        assert "123" in logs
