"""Docker container lifecycle management for sandboxed agent runs."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import docker
import docker.errors
from docker.models.containers import Container

log = logging.getLogger(__name__)

# Paths inside the container
CONTAINER_WORKSPACE = PurePosixPath("/workspace")
CONTAINER_PROMPT = CONTAINER_WORKSPACE / "prompt.md"
CONTAINER_OUTPUT = CONTAINER_WORKSPACE / "output"

# Default resource limits
DEFAULT_MEM_LIMIT = "8g"
DEFAULT_CPU_COUNT = 4
DEFAULT_DISK_LIMIT = "10g"


@dataclass
class ContainerConfig:
    """Configuration for creating an agent container."""

    image: str
    environment: dict[str, str]
    command: list[str]
    mem_limit: str = DEFAULT_MEM_LIMIT
    cpu_count: int = DEFAULT_CPU_COUNT
    network_mode: str = "none"


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
        self._client = docker.from_env()
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

    def create(self, config: ContainerConfig) -> str:
        """Create a stopped container and return its ID."""
        container: Container = self._client.containers.create(
            image=config.image,
            command=config.command,
            environment=config.environment,
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
