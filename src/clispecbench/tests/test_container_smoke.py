"""Smoke tests that run inside real Docker containers.

These tests verify that the agent container environments are functional —
tools like Bash, cmake, and g++ work correctly, and each agent CLI is
installed and runnable.  They require Docker to be running and the base
image (and, per test, the relevant agent image) to be built.

None of the tests in this file prompt an AI coding agent, so none consume
API credentials or tokens — they are all safe to run in CI.  A separate
``prompts_agent`` marker is reserved for tests that actually invoke an
agent with a real prompt.

Markers used here:

    pytest -m docker                # run only Docker smoke tests
    pytest -m "not docker"          # skip Docker smoke tests entirely
    pytest -m "not prompts_agent"   # skip only tests that prompt an agent
"""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath

import pytest

from clispecbench.agents.codex_cli import CodexCLIAdapter
from clispecbench.agents.registry import AgentSpec, get_agent_spec, list_agent_specs
from clispecbench.harness.docker import ContainerConfig, DockerSandbox
from clispecbench.harness.platform import resolve_host_home

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_IMAGE = "clispecbench-base"


def _agent_image(agent_id: str) -> str:
    return get_agent_spec(agent_id).docker_image


CONTAINER_AGENT_SPECS = [spec for spec in list_agent_specs() if spec.version_command is not None]


def _agent_spec_id(spec: AgentSpec) -> str:
    return spec.agent_id


CLAUDE_IMAGE = _agent_image("claude-code")
CODEX_IMAGE = _agent_image("codex-cli")
COPILOT_IMAGE = _agent_image("copilot-cli")
GEMINI_IMAGE = _agent_image("gemini-cli")


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
skip_no_base_image = pytest.mark.skipif(
    not _image_available(BASE_IMAGE),
    reason=f"Docker image {BASE_IMAGE} not available",
)
skip_no_claude_image = pytest.mark.skipif(
    not _image_available(CLAUDE_IMAGE),
    reason=f"Docker image {CLAUDE_IMAGE} not available",
)
skip_no_codex_image = pytest.mark.skipif(
    not _image_available(CODEX_IMAGE),
    reason=f"Docker image {CODEX_IMAGE} not available",
)
skip_no_copilot_image = pytest.mark.skipif(
    not _image_available(COPILOT_IMAGE),
    reason=f"Docker image {COPILOT_IMAGE} not available",
)
skip_no_gemini_image = pytest.mark.skipif(
    not _image_available(GEMINI_IMAGE),
    reason=f"Docker image {GEMINI_IMAGE} not available",
)


# ---------------------------------------------------------------------------
# Claude Code agent container — Bash tool functionality
# ---------------------------------------------------------------------------


@docker
@skip_no_claude_image
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
            CLAUDE_IMAGE,
            "echo hello && whoami",
            user="agent",
        )
        assert exit_code == 0, f"Basic command failed: {logs}"
        assert "hello" in logs

    def test_agent_can_mkdir_in_home(self) -> None:
        """The agent user can create directories under $HOME.

        Claude Code's Bash tool needs to create ~/.claude/session-env/.
        """
        exit_code, logs = _run_in_container(
            CLAUDE_IMAGE,
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

        from clispecbench.harness.platform import wsl_path

        with tempfile.TemporaryDirectory(prefix="claude-cred-") as cred_dir:
            cred_file = Path(cred_dir) / ".credentials.json"
            cred_file.write_text("{}")

            mount_src = str(wsl_path(cred_file))

            config = ContainerConfig(
                image=CLAUDE_IMAGE,
                environment={},
                command=[
                    "bash",
                    "-c",
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
            f"session-env creation failed with credential file mount (exit={exit_code}): {logs}"
        )

    def test_agent_can_run_cmake(self) -> None:
        """cmake is available to the agent user."""
        exit_code, logs = _run_in_container(
            CLAUDE_IMAGE,
            "cmake --version",
            user="agent",
        )
        assert exit_code == 0, f"cmake not available: {logs}"
        assert "cmake version" in logs

    def test_agent_can_run_gpp(self) -> None:
        """g++ is available to the agent user."""
        exit_code, logs = _run_in_container(
            CLAUDE_IMAGE,
            "g++-14 --version",
            user="agent",
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
                '#include <iostream>\nint main() { std::cout << "compiled ok" << std::endl; }\n'
            )

            config = ContainerConfig(
                image=CLAUDE_IMAGE,
                environment={},
                command=[
                    "bash",
                    "-c",
                    (
                        "chown agent:agent /tmp/test.cpp"
                        " && su agent -c '"
                        "g++-14 -std=c++20 -o /tmp/test /tmp/test.cpp && /tmp/test"
                        "'"
                    ),
                ],
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
# Agent CLI installation — verify each CLI is installed and runnable
# ---------------------------------------------------------------------------


@docker
class TestAgentCliInstalled:
    """Verify that each agent CLI is installed and runnable in its image.

    These tests only invoke ``<cli> --version``, which does not prompt the
    model or consume API credentials.  They are therefore NOT marked with
    ``prompts_agent`` and are safe to run in CI — they confirm that each
    agent image was built correctly and the CLI binary is on PATH.
    """

    @pytest.mark.parametrize("spec", CONTAINER_AGENT_SPECS, ids=_agent_spec_id)
    def test_agent_cli_version(self, spec: AgentSpec) -> None:
        assert spec.version_command is not None
        if not _image_available(spec.docker_image):
            pytest.skip(f"Docker image {spec.docker_image} not available")

        exit_code, logs = _run_in_container(spec.docker_image, spec.version_command)
        assert exit_code == 0, f"{spec.version_command} failed: {logs}"


# ---------------------------------------------------------------------------
# Codex CLI network isolation — live agent probes
# ---------------------------------------------------------------------------


@docker
@skip_no_base_image
class TestRestrictedEgress:
    """Network-boundary probes that do not invoke or charge an AI model."""

    def test_direct_egress_dns_and_non_allowlisted_proxy_are_blocked(self) -> None:
        config = ContainerConfig(
            image=BASE_IMAGE,
            environment={},
            command=[
                "bash",
                "-c",
                """set +e
curl --noproxy '*' -fsS --connect-timeout 3 https://1.1.1.1 >/dev/null 2>&1
printf 'DIRECT_EXIT=%s\n' "$?"
getent hosts example.com >/dev/null 2>&1
printf 'DNS_EXIT=%s\n' "$?"
curl -fsS --connect-timeout 3 https://github.com >/dev/null 2>&1
printf 'PROXY_EXIT=%s\n' "$?"
for _ in $(seq 1 24); do
    curl -fsS --connect-timeout 3 https://github.com >/dev/null 2>&1 &
done
wait
""",
            ],
            egress_allowlist=["chatgpt.com"],
        )
        sandbox = DockerSandbox()
        try:
            sandbox.create(config)
            run = sandbox.start_and_wait(30)
            logs = sandbox.get_logs()
            network_audit = sandbox.get_network_audit_logs()
        finally:
            sandbox.cleanup()

        assert run.exit_code == 0, logs
        for probe in ("DIRECT", "DNS", "PROXY"):
            match = re.search(rf"{probe}_EXIT=(\d+)", logs)
            assert match is not None, logs
            assert int(match.group(1)) != 0, logs
        audit_events = [json.loads(line) for line in network_audit.splitlines()]
        github_denials = [
            event
            for event in audit_events
            if event.get("event") == "denied" and event.get("host") == "github.com"
        ]
        assert len(github_denials) == 25


@docker
@pytest.mark.prompts_agent
@skip_no_codex_image
class TestCodexNetworkIsolation:
    """Live probes for the two Codex internet-access surfaces.

    These tests consume a small number of model tokens and are therefore
    excluded from ordinary Docker smoke runs. Run them explicitly when the
    Codex CLI or its sandbox configuration changes.
    """

    @staticmethod
    def _run_probe(tmp_path: Path, prompt: str) -> tuple[str, str]:
        adapter = CodexCLIAdapter(model="gpt-5.6-luna", effort="max")
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "prompt.md").write_text(prompt, encoding="utf-8")

        config = ContainerConfig(
            image=adapter.image_tag,
            environment=adapter.environment({}),
            command=adapter.invoke_command(
                PurePosixPath("/workspace/prompt.md"),
                PurePosixPath("/workspace"),
            ),
            volumes=adapter.credential_mounts(resolve_host_home()),
            egress_allowlist=adapter.allowed_hosts,
        )
        sandbox = DockerSandbox()
        try:
            sandbox.create(config)
            sandbox.copy_in(workspace, PurePosixPath("/workspace"))
            run = sandbox.start_and_wait(300)
            logs = sandbox.get_logs()
            network_audit = sandbox.get_network_audit_logs()
        finally:
            sandbox.cleanup()

        assert not run.timed_out, logs
        assert run.exit_code == 0, logs
        for line in network_audit.splitlines():
            assert isinstance(json.loads(line), dict)
        return logs, network_audit

    def test_model_shell_cannot_reach_public_web(self, tmp_path: Path) -> None:
        logs, network_audit = self._run_probe(
            tmp_path,
            """Use the shell exactly once to run this exact command:
curl -fsS --max-time 10 https://example.com >/dev/null; printf 'CURL_EXIT=%s\\n' "$?"
Then report the observed CURL_EXIT value. Do not use web search and do not infer the result.
""",
        )

        match = re.search(r"CURL_EXIT=(\d+)", logs)
        assert match is not None, logs
        assert int(match.group(1)) != 0, logs
        assert '"event": "denied"' in network_audit
        assert '"host": "example.com"' in network_audit

    def test_hosted_web_search_tool_is_unavailable(self, tmp_path: Path) -> None:
        logs, network_audit = self._run_probe(
            tmp_path,
            """Try to use the hosted web search tool to search for the exact query
CLISPECBENCH_NETWORK_ISOLATION_PROBE_9F4A. Do not use the shell or answer from memory.
If no hosted web search tool is available, respond exactly WEB_SEARCH_UNAVAILABLE.
""",
        )

        events: list[object] = []
        for line in logs.splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        serialized_events = json.dumps(events).lower()
        assert '"type": "web_search"' not in serialized_events
        assert '"type": "web_search_call"' not in serialized_events
        assert "WEB_SEARCH_UNAVAILABLE" in logs
        assert '"event": "allowed"' in network_audit
        assert '"host": "chatgpt.com"' in network_audit


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
            command=[
                "bash",
                "-c",
                (
                    "cd /tmp/proj/build"
                    " && cmake .. -DCMAKE_BUILD_TYPE=Release 2>&1"
                    " && cmake --build . 2>&1"
                    " && ./smoke"
                ),
            ],
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
