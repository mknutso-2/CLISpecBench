"""Tests for Docker sandbox configuration."""
# pyright: reportPrivateUsage=false, reportUnknownMemberType=false

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from docker import errors as docker_errors

from swe_buildbench.harness.docker import ContainerConfig, _resolve_docker_client


class TestContainerConfig:
    def test_default_network_is_bridge(self) -> None:
        config = ContainerConfig(image="test", environment={}, command=["echo"])
        assert config.network_mode == "bridge"

    def test_volumes_default_empty(self) -> None:
        config = ContainerConfig(image="test", environment={}, command=["echo"])
        assert config.volumes == {}

    def test_volumes_can_be_set(self) -> None:
        vols = {"/host/path": {"bind": "/container/path", "mode": "ro"}}
        config = ContainerConfig(
            image="test", environment={}, command=["echo"], volumes=vols
        )
        assert config.volumes == vols


class TestResolveDockerClient:
    def test_returns_default_client_when_from_env_succeeds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client = Mock()
        client.ping.return_value = None
        monkeypatch.setattr("swe_buildbench.harness.docker.docker.from_env", lambda: client)

        resolved = _resolve_docker_client()

        assert resolved is client
        client.ping.assert_called_once_with()

    def test_windows_falls_back_to_tcp_when_default_client_fails(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        default_error = docker_errors.DockerException("npipe unavailable")
        tcp_client = Mock()
        tcp_client.ping.return_value = None

        monkeypatch.setattr("swe_buildbench.harness.docker.sys.platform", "win32")
        monkeypatch.setenv("DOCKER_HOST", "npipe:////./pipe/docker_engine")
        monkeypatch.setenv("DOCKER_CONTEXT", "desktop-linux")
        monkeypatch.setattr(
            "swe_buildbench.harness.docker.docker.from_env",
            Mock(side_effect=default_error),
        )
        docker_client_ctor = Mock(return_value=tcp_client)
        monkeypatch.setattr(
            "swe_buildbench.harness.docker.DockerClient",
            docker_client_ctor,
        )

        with caplog.at_level(logging.INFO):
            resolved = _resolve_docker_client()

        assert resolved is tcp_client
        tcp_client.ping.assert_called_once_with()
        docker_client_ctor.assert_called_once_with(base_url="tcp://localhost:2375")
        assert "Docker default connection attempt failed" in caplog.text
        assert "DOCKER_HOST=npipe:////./pipe/docker_engine" in caplog.text
        assert "DOCKER_CONTEXT=desktop-linux" in caplog.text
        assert "npipe unavailable" in caplog.text
        assert "WARNING" not in caplog.text

    def test_windows_failure_message_includes_both_attempts_and_env(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        default_error = docker_errors.DockerException("CreateFile missing")
        tcp_error = docker_errors.DockerException("connection refused")

        monkeypatch.setattr("swe_buildbench.harness.docker.sys.platform", "win32")
        monkeypatch.delenv("DOCKER_HOST", raising=False)
        monkeypatch.delenv("DOCKER_CONTEXT", raising=False)
        monkeypatch.setattr(
            "swe_buildbench.harness.docker.docker.from_env",
            Mock(side_effect=default_error),
        )
        tcp_client = SimpleNamespace(ping=Mock(side_effect=tcp_error))
        monkeypatch.setattr(
            "swe_buildbench.harness.docker.DockerClient",
            Mock(return_value=tcp_client),
        )

        with caplog.at_level(logging.WARNING), pytest.raises(
            docker_errors.DockerException
        ) as exc_info:
            _resolve_docker_client()

        message = str(exc_info.value)
        assert "platform=win32" in message
        assert "DOCKER_HOST=<unset>" in message
        assert "DOCKER_CONTEXT=<unset>" in message
        assert "default client failed: DockerException: CreateFile missing" in message
        assert "tcp fallback failed: DockerException: connection refused" in message
        assert "Docker TCP fallback connection attempt failed" in caplog.text
        assert exc_info.value.__cause__ is tcp_error

    def test_linux_failure_message_includes_default_attempt_details(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        default_error = docker_errors.DockerException("unix socket missing")

        monkeypatch.setattr("swe_buildbench.harness.docker.sys.platform", "linux")
        monkeypatch.delenv("DOCKER_HOST", raising=False)
        monkeypatch.delenv("DOCKER_CONTEXT", raising=False)
        monkeypatch.setattr(
            "swe_buildbench.harness.docker.docker.from_env",
            Mock(side_effect=default_error),
        )

        with caplog.at_level(logging.WARNING), pytest.raises(
            docker_errors.DockerException
        ) as exc_info:
            _resolve_docker_client()

        message = str(exc_info.value)
        assert "platform=linux" in message
        assert "DOCKER_HOST=<unset>" in message
        assert "DOCKER_CONTEXT=<unset>" in message
        assert "default client failed: DockerException: unix socket missing" in message
        assert "set DOCKER_HOST and retry" in message
        assert "Docker default connection attempt failed" in caplog.text
        assert exc_info.value.__cause__ is default_error

    def test_empty_docker_env_values_are_reported_as_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        default_error = docker_errors.DockerException("unix socket missing")

        monkeypatch.setattr("swe_buildbench.harness.docker.sys.platform", "linux")
        monkeypatch.setenv("DOCKER_HOST", "")
        monkeypatch.setenv("DOCKER_CONTEXT", "")
        monkeypatch.setattr(
            "swe_buildbench.harness.docker.docker.from_env",
            Mock(side_effect=default_error),
        )

        with pytest.raises(docker_errors.DockerException) as exc_info:
            _resolve_docker_client()

        message = str(exc_info.value)
        assert "DOCKER_HOST=<empty>" in message
        assert "DOCKER_CONTEXT=<empty>" in message
