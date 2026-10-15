"""Tests for passing secrets such as a `claude setup-token` token into containers."""

from __future__ import annotations

from pathlib import Path

import pytest

from clispecbench.agents.claude_code import OAUTH_TOKEN_ENV, ClaudeCodeAdapter
from clispecbench.agents.codex_cli import CodexCLIAdapter
from clispecbench.cli import collect_secret_env

HOME = Path("/synthetic-home")
CREDENTIALS = (HOME / ".claude" / ".credentials.json").as_posix()
SETTINGS = (HOME / ".claude" / "settings.json").as_posix()


def test_secret_env_copies_named_values_from_the_environment() -> None:
    environ = {OAUTH_TOKEN_ENV: "sk-ant-oat01-synthetic", "UNRELATED": "x"}

    assert collect_secret_env([OAUTH_TOKEN_ENV], environ) == {
        OAUTH_TOKEN_ENV: "sk-ant-oat01-synthetic"
    }
    assert collect_secret_env([], environ) == {}


@pytest.mark.parametrize("environ", [{}, {OAUTH_TOKEN_ENV: ""}])
def test_secret_env_rejects_missing_values_without_revealing_others(
    environ: dict[str, str],
) -> None:
    with pytest.raises(ValueError, match=OAUTH_TOKEN_ENV) as excinfo:
        collect_secret_env([OAUTH_TOKEN_ENV], {**environ, "OTHER": "sk-secret"})

    assert "sk-secret" not in str(excinfo.value)


@pytest.mark.parametrize("model", ["claude-sonnet-5-5", "claude-opus-5-5", "claude-haiku-5-5"])
def test_oauth_token_replaces_the_login_credentials_mount(model: str) -> None:
    adapter = ClaudeCodeAdapter(model=model)
    environment = adapter.environment({OAUTH_TOKEN_ENV: "sk-ant-oat01-synthetic"})

    mounts = adapter.credential_mounts_for(HOME, environment)

    assert environment[OAUTH_TOKEN_ENV] == "sk-ant-oat01-synthetic"
    assert CREDENTIALS not in mounts
    assert mounts[SETTINGS] == {"bind": "/home/agent/.claude/settings.json", "mode": "ro"}


def test_login_credentials_stay_mounted_without_a_token() -> None:
    adapter = ClaudeCodeAdapter(model="claude-sonnet-5-5")

    assert adapter.credential_mounts_for(HOME, adapter.environment({})) == (
        adapter.credential_mounts(HOME)
    )
    assert CREDENTIALS in adapter.credential_mounts_for(HOME, adapter.environment({}))


def test_other_agents_ignore_the_claude_token() -> None:
    adapter = CodexCLIAdapter(model="gpt-6.1-sol")
    environment = {OAUTH_TOKEN_ENV: "sk-ant-oat01-synthetic"}

    assert adapter.credential_mounts_for(HOME, environment) == adapter.credential_mounts(HOME)
