"""Tests for agent adapters: credentials, version, model/effort."""
# pyright: reportUnknownMemberType=false

from __future__ import annotations

from pathlib import Path, PurePosixPath

from swe_buildbench.agents.claude_code import ClaudeCodeAdapter
from swe_buildbench.agents.codex_cli import CodexCLIAdapter
from swe_buildbench.agents.gemini_cli import GeminiCLIAdapter


class TestClaudeCodeCredentialMounts:
    def test_mounts_claude_dir_and_config(self) -> None:
        adapter = ClaudeCodeAdapter()
        mounts = adapter.credential_mounts(Path("/home/user"))
        assert "/home/user/.claude" in mounts
        assert mounts["/home/user/.claude"]["bind"] == "/home/agent/.claude"
        assert mounts["/home/user/.claude"]["mode"] == "ro"
        assert "/home/user/.claude.json" in mounts
        assert mounts["/home/user/.claude.json"]["bind"] == "/home/agent/.claude.json"


class TestCodexCLICredentialMounts:
    def test_mounts_auth_json_only(self) -> None:
        adapter = CodexCLIAdapter()
        mounts = adapter.credential_mounts(Path("/home/user"))
        assert len(mounts) == 1
        key = "/home/user/.codex/auth.json"
        assert key in mounts
        assert mounts[key]["bind"] == "/root/.codex/auth.json"
        assert mounts[key]["mode"] == "ro"


class TestGeminiCLICredentialMounts:
    def test_mounts_three_files_to_staging(self) -> None:
        adapter = GeminiCLIAdapter()
        mounts = adapter.credential_mounts(Path("/home/user"))
        assert len(mounts) == 3
        for filename in ("oauth_creds.json", "google_accounts.json", "settings.json"):
            key = f"/home/user/.gemini/{filename}"
            assert key in mounts, f"Missing mount for {filename}"
            assert mounts[key]["bind"].startswith("/tmp/gemini-auth/")
            assert mounts[key]["mode"] == "ro"

    def test_invoke_command_copies_credentials(self) -> None:
        adapter = GeminiCLIAdapter()
        cmd = adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"),
            PurePosixPath("/workspace"),
        )
        # The bash command should copy from staging and seed projects.json
        bash_script = cmd[2]
        assert "cp /tmp/gemini-auth/*" in bash_script
        assert "projects.json" in bash_script
        assert "--yolo" in bash_script
        assert "--output-format stream-json" in bash_script


class TestAgentVersions:
    def test_claude_code_version_from_dockerfile(self) -> None:
        adapter = ClaudeCodeAdapter()
        assert adapter.version != "unknown"
        # Should be a semver-like string
        assert "." in adapter.version

    def test_codex_cli_version_from_dockerfile(self) -> None:
        adapter = CodexCLIAdapter()
        assert adapter.version != "unknown"
        assert "." in adapter.version

    def test_gemini_cli_version_from_dockerfile(self) -> None:
        adapter = GeminiCLIAdapter()
        assert adapter.version != "unknown"
        assert "." in adapter.version


class TestModelAndEffort:
    def test_claude_code_model_in_command(self) -> None:
        adapter = ClaudeCodeAdapter(model="sonnet", effort="high")
        cmd = adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"),
            PurePosixPath("/workspace"),
        )
        bash_script = cmd[2]
        assert "--model sonnet" in bash_script
        assert "--effort high" in bash_script

    def test_claude_code_no_model_flags_by_default(self) -> None:
        adapter = ClaudeCodeAdapter()
        cmd = adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"),
            PurePosixPath("/workspace"),
        )
        bash_script = cmd[2]
        assert "--model" not in bash_script
        assert "--effort" not in bash_script

    def test_codex_model_in_command(self) -> None:
        adapter = CodexCLIAdapter(model="o3")
        cmd = adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"),
            PurePosixPath("/workspace"),
        )
        bash_script = cmd[2]
        assert '--model "o3"' in bash_script

    def test_gemini_model_in_command(self) -> None:
        adapter = GeminiCLIAdapter(model="gemini-2.5-pro")
        cmd = adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"),
            PurePosixPath("/workspace"),
        )
        bash_script = cmd[2]
        assert '--model "gemini-2.5-pro"' in bash_script
        assert "--yolo" in bash_script

    def test_adapter_model_property(self) -> None:
        adapter = ClaudeCodeAdapter(model="opus")
        assert adapter.model == "opus"
        assert adapter.effort is None

    def test_adapter_effort_property(self) -> None:
        adapter = ClaudeCodeAdapter(effort="max")
        assert adapter.effort == "max"
        assert adapter.model is None


class TestTelemetryPaths:
    def test_claude_code_has_otel_path(self) -> None:
        adapter = ClaudeCodeAdapter()
        assert any("otel" in p for p in adapter.telemetry_paths)

    def test_codex_has_event_log_path(self) -> None:
        adapter = CodexCLIAdapter()
        assert any("codex-events" in p for p in adapter.telemetry_paths)

    def test_gemini_has_no_telemetry_paths(self) -> None:
        adapter = GeminiCLIAdapter()
        assert adapter.telemetry_paths == []
