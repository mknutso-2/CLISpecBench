"""Tests for runner failure artifact behavior."""
# pyright: reportPrivateUsage=false, reportUnknownMemberType=false

from __future__ import annotations

from pathlib import Path, PurePosixPath

import pytest
from docker import errors as docker_errors
from requests import exceptions as requests_exceptions

from clispecbench.agents.base import AgentAdapter
from clispecbench.harness.results import load_result
from clispecbench.harness.runner import run_evaluation
from clispecbench.harness.task import TaskDefinition


class _StubAdapter(AgentAdapter):
    @property
    def name(self) -> str:
        return "codex-cli"

    @property
    def version(self) -> str:
        return "1.2.3"

    @property
    def model(self) -> str:
        return "gpt-5.3-codex"

    @property
    def effort(self) -> str:
        return "xhigh"

    @property
    def dockerfile(self) -> Path:
        return Path("docker/agents/codex-cli.Dockerfile")

    @property
    def image_tag(self) -> str:
        return "clispecbench-codex-cli"

    @property
    def telemetry_paths(self) -> list[str]:
        return []

    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        return {}

    def invoke_command(
        self, prompt_path: PurePosixPath, work_dir: PurePosixPath
    ) -> list[str]:
        return ["codex", "exec"]

    def parse_token_usage(self, container_fs: Path, container_logs: str = "") -> None:
        return None

    def credential_mounts(self, host_home: Path) -> dict[str, dict[str, str]]:
        return {}

    def extract_last_agent_message(self, container_logs: str) -> None:
        return None


def _stub_task(root: Path) -> TaskDefinition:
    return TaskDefinition(
        task_id="stubtask-cpp",
        root=root,
        base_prompt_path=root / "base.md",
        language_prompt_path=root / "lang.md",
        technical_prompt_path=root / "technical.md",
        docs_dir=root,
        test_dir=root,
        version="2.1.1",
        language="cpp",
    )


class _StubHash:
    def __init__(self, sha256: str) -> None:
        self.sha256 = sha256


def _fake_prompt_hash(task: TaskDefinition, prompt_variant: str | None) -> _StubHash:
    del task, prompt_variant
    return _StubHash("prompt-sha")


def _fake_test_hash(task: TaskDefinition) -> _StubHash:
    del task
    return _StubHash("tests-sha")


def _fake_workspace(task: TaskDefinition, prompt_variant: str | None, workspace: Path) -> Path:
    del task, prompt_variant
    return workspace


def test_docker_init_failure_writes_minimal_result_then_reraises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _stub_task(tmp_path)
    adapter = _StubAdapter()
    default_error = docker_errors.DockerException(
        "Cannot connect to Docker daemon.\n"
        "  platform=win32\n"
        "  DOCKER_HOST=<unset>\n"
        "  default client failed: DockerException: CreateFile missing\n"
        "  tcp fallback failed: DockerException: connection refused"
    )

    class _FailingSandbox:
        def __init__(self) -> None:
            raise default_error

    monkeypatch.setattr("clispecbench.harness.runner.DockerSandbox", _FailingSandbox)
    monkeypatch.setattr(
        "clispecbench.harness.runner.hash_prompt_content",
        _fake_prompt_hash,
    )
    monkeypatch.setattr(
        "clispecbench.harness.runner.hash_test_suite",
        _fake_test_hash,
    )
    monkeypatch.setattr("clispecbench.harness.runner._git_sha", lambda: "abc1234")
    monkeypatch.setattr("clispecbench.harness.runner._harness_version", lambda: "0.1.0")

    with pytest.raises(docker_errors.DockerException) as exc_info:
        run_evaluation(
            task=task,
            adapter=adapter,
            run_number=1,
            eval_number=7,
            output_dir=tmp_path,
        )

    assert exc_info.value is default_error

    result_json = (
        tmp_path
        / "stubtask-cpp"
        / "codex-cli"
        / "gpt-5.3-codex_xhigh"
        / "eval7"
        / "run1"
        / "result.json"
    )
    assert result_json.is_file()

    result = load_result(result_json)
    assert result.metadata.exit_reason == "error"
    assert result.metadata.notes == (
        "infrastructure_failure: Docker unavailable before scoring completed"
    )
    assert result.metadata.docker_image_sha == "unknown"
    assert result.build.success is False
    assert "Cannot connect to Docker daemon." in result.build.diagnostics
    assert result.test_summary.total == 0
    assert result.scores.task_score is None
    assert result.artifacts.transcript is None


def test_docker_failure_after_sandbox_init_preserves_image_sha_in_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _stub_task(tmp_path)
    adapter = _StubAdapter()
    docker_error = docker_errors.DockerException("daemon went away")
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    class _Sandbox:
        def image_exists(self, tag: str) -> bool:
            raise docker_error

        def get_image_sha(self, tag: str) -> str:
            return "sha256:test-image"

        def cleanup(self) -> None:
            return None

    monkeypatch.setattr("clispecbench.harness.runner.DockerSandbox", _Sandbox)
    monkeypatch.setattr(
        "clispecbench.harness.runner.hash_prompt_content",
        _fake_prompt_hash,
    )
    monkeypatch.setattr(
        "clispecbench.harness.runner.hash_test_suite",
        _fake_test_hash,
    )
    monkeypatch.setattr("clispecbench.harness.runner._git_sha", lambda: "abc1234")
    monkeypatch.setattr("clispecbench.harness.runner._harness_version", lambda: "0.1.0")

    def _prepare_workspace(task: TaskDefinition, prompt_variant: str | None) -> Path:
        return _fake_workspace(task, prompt_variant, workspace)

    monkeypatch.setattr(
        "clispecbench.harness.runner.prepare_workspace",
        _prepare_workspace,
    )

    with pytest.raises(docker_errors.DockerException) as exc_info:
        run_evaluation(
            task=task,
            adapter=adapter,
            run_number=2,
            eval_number=3,
            output_dir=tmp_path,
        )

    assert exc_info.value is docker_error

    result_json = (
        tmp_path
        / "stubtask-cpp"
        / "codex-cli"
        / "gpt-5.3-codex_xhigh"
        / "eval3"
        / "run2"
        / "result.json"
    )
    result = load_result(result_json)
    assert result.metadata.docker_image_sha == "sha256:test-image"
    assert result.build.diagnostics == "daemon went away"


def test_docker_failure_result_falls_back_to_unknown_image_sha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _stub_task(tmp_path)
    adapter = _StubAdapter()
    docker_error = docker_errors.DockerException("daemon went away")
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    class _Sandbox:
        def image_exists(self, tag: str) -> bool:
            raise docker_error

        def get_image_sha(self, tag: str) -> str:
            raise RuntimeError("sha lookup failed")

        def cleanup(self) -> None:
            return None

    monkeypatch.setattr("clispecbench.harness.runner.DockerSandbox", _Sandbox)
    monkeypatch.setattr(
        "clispecbench.harness.runner.hash_prompt_content",
        _fake_prompt_hash,
    )
    monkeypatch.setattr(
        "clispecbench.harness.runner.hash_test_suite",
        _fake_test_hash,
    )
    monkeypatch.setattr("clispecbench.harness.runner._git_sha", lambda: "abc1234")
    monkeypatch.setattr("clispecbench.harness.runner._harness_version", lambda: "0.1.0")

    def _prepare_workspace(task: TaskDefinition, prompt_variant: str | None) -> Path:
        return _fake_workspace(task, prompt_variant, workspace)

    monkeypatch.setattr(
        "clispecbench.harness.runner.prepare_workspace",
        _prepare_workspace,
    )

    with pytest.raises(docker_errors.DockerException):
        run_evaluation(
            task=task,
            adapter=adapter,
            run_number=3,
            eval_number=5,
            output_dir=tmp_path,
        )

    result_json = (
        tmp_path
        / "stubtask-cpp"
        / "codex-cli"
        / "gpt-5.3-codex_xhigh"
        / "eval5"
        / "run3"
        / "result.json"
    )
    result = load_result(result_json)
    assert result.metadata.docker_image_sha == "unknown"


def test_build_error_uses_specific_infrastructure_failure_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _stub_task(tmp_path)
    adapter = _StubAdapter()
    build_error = docker_errors.BuildError("bad dockerfile", build_log=iter(()))
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    class _Sandbox:
        def image_exists(self, tag: str) -> bool:
            return False

        def build_image(self, dockerfile: Path, tag: str) -> str:
            raise build_error

        def get_image_sha(self, tag: str) -> str:
            return "unknown"

        def cleanup(self) -> None:
            return None

    monkeypatch.setattr("clispecbench.harness.runner.DockerSandbox", _Sandbox)
    monkeypatch.setattr(
        "clispecbench.harness.runner.hash_prompt_content",
        _fake_prompt_hash,
    )
    monkeypatch.setattr(
        "clispecbench.harness.runner.hash_test_suite",
        _fake_test_hash,
    )
    monkeypatch.setattr("clispecbench.harness.runner._git_sha", lambda: "abc1234")
    monkeypatch.setattr("clispecbench.harness.runner._harness_version", lambda: "0.1.0")

    def _prepare_workspace(task: TaskDefinition, prompt_variant: str | None) -> Path:
        return _fake_workspace(task, prompt_variant, workspace)

    monkeypatch.setattr(
        "clispecbench.harness.runner.prepare_workspace",
        _prepare_workspace,
    )

    with pytest.raises(docker_errors.BuildError):
        run_evaluation(
            task=task,
            adapter=adapter,
            run_number=4,
            eval_number=6,
            output_dir=tmp_path,
        )

    result_json = (
        tmp_path
        / "stubtask-cpp"
        / "codex-cli"
        / "gpt-5.3-codex_xhigh"
        / "eval6"
        / "run4"
        / "result.json"
    )
    result = load_result(result_json)
    assert result.metadata.notes == (
        "infrastructure_failure: Docker image build failed before scoring completed"
    )


def test_request_exception_uses_specific_infrastructure_failure_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _stub_task(tmp_path)
    adapter = _StubAdapter()
    request_error = requests_exceptions.ConnectionError("connection reset")
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    class _Sandbox:
        def image_exists(self, tag: str) -> bool:
            raise request_error

        def get_image_sha(self, tag: str) -> str:
            return "unknown"

        def cleanup(self) -> None:
            return None

    monkeypatch.setattr("clispecbench.harness.runner.DockerSandbox", _Sandbox)
    monkeypatch.setattr(
        "clispecbench.harness.runner.hash_prompt_content",
        _fake_prompt_hash,
    )
    monkeypatch.setattr(
        "clispecbench.harness.runner.hash_test_suite",
        _fake_test_hash,
    )
    monkeypatch.setattr("clispecbench.harness.runner._git_sha", lambda: "abc1234")
    monkeypatch.setattr("clispecbench.harness.runner._harness_version", lambda: "0.1.0")

    def _prepare_workspace(task: TaskDefinition, prompt_variant: str | None) -> Path:
        return _fake_workspace(task, prompt_variant, workspace)

    monkeypatch.setattr(
        "clispecbench.harness.runner.prepare_workspace",
        _prepare_workspace,
    )

    with pytest.raises(requests_exceptions.ConnectionError):
        run_evaluation(
            task=task,
            adapter=adapter,
            run_number=5,
            eval_number=8,
            output_dir=tmp_path,
        )

    result_json = (
        tmp_path
        / "stubtask-cpp"
        / "codex-cli"
        / "gpt-5.3-codex_xhigh"
        / "eval8"
        / "run5"
        / "result.json"
    )
    result = load_result(result_json)
    assert result.metadata.notes == (
        "infrastructure_failure: Docker request error before scoring completed"
    )
