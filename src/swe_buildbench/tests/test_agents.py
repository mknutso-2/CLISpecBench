"""Tests for agent adapter credential mounts."""
# pyright: reportUnknownMemberType=false

from __future__ import annotations

from pathlib import Path

from swe_buildbench.agents.claude_code import ClaudeCodeAdapter
from swe_buildbench.agents.codex_cli import CodexCLIAdapter
from swe_buildbench.agents.gemini_cli import GeminiCLIAdapter


class TestClaudeCodeCredentialMounts:
    def test_mounts_claude_dir_and_config(self) -> None:
        adapter = ClaudeCodeAdapter()
        mounts = adapter.credential_mounts(Path("/home/user"))
        assert "/home/user/.claude" in mounts
        assert mounts["/home/user/.claude"]["bind"] == "/root/.claude"
        assert mounts["/home/user/.claude"]["mode"] == "ro"
        assert "/home/user/.claude.json" in mounts
        assert mounts["/home/user/.claude.json"]["bind"] == "/root/.claude.json"


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
        from pathlib import PurePosixPath

        adapter = GeminiCLIAdapter()
        cmd = adapter.invoke_command(
            PurePosixPath("/workspace/prompt.md"),
            PurePosixPath("/workspace"),
        )
        # The bash command should copy from staging and seed projects.json
        bash_script = cmd[2]
        assert "cp /tmp/gemini-auth/*" in bash_script
        assert "projects.json" in bash_script
