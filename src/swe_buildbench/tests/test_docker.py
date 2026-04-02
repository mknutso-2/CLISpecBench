"""Tests for Docker sandbox configuration."""
# pyright: reportUnknownMemberType=false

from __future__ import annotations

from swe_buildbench.harness.docker import ContainerConfig


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
