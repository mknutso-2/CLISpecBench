"""Docker container lifecycle management for sandboxed agent runs."""

from __future__ import annotations

import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

import docker
import docker.errors
from docker import DockerClient
from docker.models.containers import Container

log = logging.getLogger(__name__)

# Paths inside the container
CONTAINER_WORKSPACE = PurePosixPath("/workspace")
CONTAINER_PROMPT = CONTAINER_WORKSPACE / "prompt.md"
CONTAINER_OUTPUT = CONTAINER_WORKSPACE / "output"

# Default resource limits.  ``DEFAULT_CPU_COUNT`` is the per-container ``--cpus``
# limit applied via ``nano_cpus`` at create-time, NOT a request for that many
# CPUs.  Docker rejects values larger than the host's CPU count with a 400 Bad
# Request, so we cap at whatever the host actually has — this lets the same
# default work on bigger dev machines and on smaller CI runners (GHA
# ubuntu-latest has 2 cores).
DEFAULT_MEM_LIMIT = "8g"
DEFAULT_CPU_COUNT = min(4, os.cpu_count() or 4)
DEFAULT_DISK_LIMIT = "10g"


def _docker_env_value(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        return "<unset>"
    if value == "":
        return "<empty>"
    return value


def _describe_docker_exception(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def _resolve_docker_client() -> DockerClient:
    """Create a Docker client, handling Windows-WSL and native Linux.

    Resolution order:
    1. ``docker.from_env()`` — works on native Linux (Unix socket) and when
       ``DOCKER_HOST`` is already set.
    2. On Windows, try ``tcp://localhost:2375`` — works when the WSL2 Docker
       daemon is configured to listen on TCP (see ``scripts/install-docker-wsl.sh``).
    3. Raise with a helpful error message.
    """
    platform = sys.platform
    docker_host = _docker_env_value("DOCKER_HOST")
    docker_context = _docker_env_value("DOCKER_CONTEXT")

    # Attempt 1: standard detection (env vars, default socket)
    try:
        client = docker.from_env()
        client.ping()  # pyright: ignore[reportUnknownMemberType]
        log.debug("Docker connected via default environment")
        return client
    except docker.errors.DockerException as exc:
        default_error = exc
        log_fn = log.info if platform == "win32" else log.warning
        log_fn(
            "Docker default connection attempt failed "
            "(platform=%s, DOCKER_HOST=%s, DOCKER_CONTEXT=%s): %s",
            platform,
            docker_host,
            docker_context,
            _describe_docker_exception(exc),
        )
        if platform != "win32":
            msg = (
                "Cannot connect to Docker daemon.\n"
                f"  platform={platform}\n"
                f"  DOCKER_HOST={docker_host}\n"
                f"  DOCKER_CONTEXT={docker_context}\n"
                f"  default client failed: {_describe_docker_exception(default_error)}\n"
                "  - On Linux/macOS: ensure Docker is running and the current "
                "endpoint is reachable.\n"
                "  - If you rely on a non-default Docker endpoint, set DOCKER_HOST "
                "and retry."
            )
            raise docker.errors.DockerException(msg) from exc

    # Attempt 2: Windows — try TCP to WSL2 Docker daemon
    tcp_url = "tcp://localhost:2375"
    try:
        client = DockerClient(base_url=tcp_url)
        client.ping()  # pyright: ignore[reportUnknownMemberType]
        log.info("Docker connected via %s (WSL2)", tcp_url)
        return client
    except docker.errors.DockerException as exc:
        tcp_error = exc
        log.warning(
            "Docker TCP fallback connection attempt failed (base_url=%s): %s",
            tcp_url,
            _describe_docker_exception(exc),
        )

    msg = (
        "Cannot connect to Docker daemon.\n"
        f"  platform={platform}\n"
        f"  DOCKER_HOST={docker_host}\n"
        f"  DOCKER_CONTEXT={docker_context}\n"
        f"  default client failed: {_describe_docker_exception(default_error)}\n"
        f"  tcp fallback failed: {_describe_docker_exception(tcp_error)}\n"
        "  - On Linux/macOS: ensure Docker is running and the current endpoint "
        "is reachable.\n"
        "  - On Windows (WSL2): either set DOCKER_HOST=tcp://localhost:2375\n"
        "    or configure the WSL2 Docker daemon to listen on TCP.\n"
        "    See scripts/install-docker-wsl.sh for setup instructions."
    )
    raise docker.errors.DockerException(msg) from tcp_error


@dataclass
class ContainerConfig:
    """Configuration for creating an agent container."""

    image: str
    environment: dict[str, str]
    command: list[str]
    volumes: dict[str, dict[str, str]] = field(default_factory=dict[str, dict[str, str]])
    mem_limit: str = DEFAULT_MEM_LIMIT
    cpu_count: int = DEFAULT_CPU_COUNT
    network_mode: str = "bridge"


@dataclass
class ContainerRun:
    """Result of running an agent in a container."""

    exit_code: int | None
    timed_out: bool
    wall_clock_seconds: float
    container_id: str


class DockerSandbox:
    """Manages the lifecycle of a sandboxed Docker container for one agent run."""

    def __init__(self) -> None:
        self._client = _resolve_docker_client()
        self._container: Container | None = None

    def build_image(self, dockerfile: Path, tag: str) -> str:
        """Build (or rebuild) a Docker image from a Dockerfile.

        Returns the image tag.
        """
        context = str(dockerfile.parent)
        log.info("Building Docker image %s from %s", tag, context)
        image, _logs = self._client.images.build(
            path=context,
            dockerfile=dockerfile.name,
            tag=tag,
            rm=True,
        )
        return str(image.tags[0]) if image.tags else tag

    def image_exists(self, tag: str) -> bool:
        """Check whether a Docker image with the given tag exists locally."""
        try:
            self._client.images.get(tag)
            return True
        except docker.errors.ImageNotFound:
            return False

    def get_image_sha(self, tag: str) -> str:
        """Return the image ID (sha256 digest) for the given tag."""
        try:
            image = self._client.images.get(tag)
            return str(image.id)
        except docker.errors.ImageNotFound:
            return "unknown"

    def create(self, config: ContainerConfig) -> str:
        """Create a stopped container and return its ID."""
        container: Container = self._client.containers.create(
            image=config.image,
            command=config.command,
            environment=config.environment,
            volumes=config.volumes or None,
            mem_limit=config.mem_limit,
            nano_cpus=config.cpu_count * 10**9,
            network_mode=config.network_mode,
            working_dir=str(CONTAINER_WORKSPACE),
            detach=True,
        )
        self._container = container
        log.info("Created container %s (image=%s)", container.short_id, config.image)
        return str(container.id)

    def copy_in(self, host_path: Path, container_path: PurePosixPath) -> None:
        """Copy a file or directory from the host into the container."""
        if self._container is None:
            raise RuntimeError("No container created")
        import io
        import tarfile

        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            tar.add(str(host_path), arcname=container_path.name)
        buf.seek(0)
        self._container.put_archive(str(container_path.parent), buf)  # pyright: ignore[reportUnknownMemberType]

    def start_and_wait(self, timeout_seconds: float) -> ContainerRun:
        """Start the container and wait for it to finish or timeout.

        If the container exceeds *timeout_seconds*, it is killed.
        """
        if self._container is None:
            raise RuntimeError("No container created")

        t0 = time.monotonic()
        self._container.start()
        log.info("Container %s started", self._container.short_id)

        timed_out = False
        try:
            result = self._container.wait(timeout=timeout_seconds)
            exit_code: int | None = result.get("StatusCode")
        except Exception:
            # Timeout or connection error — kill the container
            log.warning(
                "Container %s exceeded timeout of %.0fs, killing",
                self._container.short_id,
                timeout_seconds,
            )
            self._container.kill()
            timed_out = True
            exit_code = None

        elapsed = time.monotonic() - t0
        return ContainerRun(
            exit_code=exit_code,
            timed_out=timed_out,
            wall_clock_seconds=elapsed,
            container_id=str(self._container.id),
        )

    def copy_out(self, container_path: PurePosixPath, host_path: Path) -> None:
        """Copy a file or directory from the container to the host."""
        if self._container is None:
            raise RuntimeError("No container created")
        import io
        import tarfile

        stream, _stat = self._container.get_archive(str(container_path))
        buf = io.BytesIO()
        for chunk in stream:
            buf.write(chunk)
        buf.seek(0)

        host_path.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=buf) as tar:
            tar.extractall(path=str(host_path))

    def cleanup(self) -> None:
        """Remove the container."""
        if self._container is None:
            return
        try:
            self._container.remove(force=True)
            log.info("Removed container %s", self._container.short_id)
        except docker.errors.NotFound:
            pass
        self._container = None

    def get_logs(self) -> str:
        """Return stdout + stderr logs from the container."""
        if self._container is None:
            raise RuntimeError("No container created")
        raw: bytes = self._container.logs()
        return raw.decode("utf-8", errors="replace")

    def run_oneshot(
        self,
        config: ContainerConfig,
        timeout_seconds: float,
    ) -> tuple[int | None, str]:
        """Create, start, wait, and return (exit_code, logs) for a one-shot container.

        The container is removed after use regardless of outcome.
        """
        prev = self._container
        try:
            self.create(config)
            run = self.start_and_wait(timeout_seconds)
            logs = self.get_logs()
            return run.exit_code, logs
        finally:
            if self._container is not None:
                self.cleanup()
            self._container = prev
