"""Docker container lifecycle management for sandboxed agent runs."""

from __future__ import annotations

import json
import logging
import os
import socket
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

import docker
import docker.errors
from docker import DockerClient
from docker.models.containers import Container
from docker.models.networks import Network
from requests import exceptions as requests_exceptions
from urllib3 import exceptions as urllib3_exceptions

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

EGRESS_PROXY_PORT = 3128
_EGRESS_PROXY_SOURCE = r'''
import json
import selectors
import socket
import socketserver
import sys
import threading
import time

PORT = int(sys.argv[1])
ALLOWED_HOSTS = tuple(json.loads(sys.argv[2]))
EMIT_LOCK = threading.Lock()


def emit(event, **fields):
    line = json.dumps({"event": event, "timestamp": time.time(), **fields})
    # Proxy handlers run concurrently. Serialize the complete line and flush
    # while holding one lock so Docker's combined log is valid JSONL.
    with EMIT_LOCK:
        sys.stdout.write(line + "\n")
        sys.stdout.flush()


def allowed(host, port):
    host = host.rstrip(".").lower()
    return port == 443 and any(
        host == suffix or host.endswith("." + suffix) for suffix in ALLOWED_HOSTS
    )


def split_authority(authority):
    if authority.startswith("["):
        host, _, remainder = authority[1:].partition("]")
        port = int(remainder[1:]) if remainder.startswith(":") else 443
        return host, port
    host, separator, raw_port = authority.rpartition(":")
    if not separator:
        return authority, 443
    return host, int(raw_port)


def relay(client, upstream):
    selector = selectors.DefaultSelector()
    selector.register(client, selectors.EVENT_READ, upstream)
    selector.register(upstream, selectors.EVENT_READ, client)
    while selector.get_map():
        for key, _ in selector.select(timeout=60):
            source = key.fileobj
            destination = key.data
            data = source.recv(65536)
            if not data:
                return
            destination.sendall(data)


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(30)
        header = b""
        while b"\r\n\r\n" not in header and len(header) < 65536:
            chunk = self.request.recv(4096)
            if not chunk:
                return
            header += chunk
        try:
            first_line = header.split(b"\r\n", 1)[0].decode("ascii")
            method, authority, _ = first_line.split(" ", 2)
            host, port = split_authority(authority)
        except (UnicodeDecodeError, ValueError):
            emit("denied", reason="malformed_request", client=self.client_address[0])
            self.request.sendall(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n")
            return

        normalized_host = host.rstrip(".").lower()
        if method.upper() != "CONNECT" or not allowed(normalized_host, port):
            emit(
                "denied",
                host=normalized_host,
                port=port,
                method=method.upper(),
                client=self.client_address[0],
            )
            self.request.sendall(b"HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n")
            return

        try:
            upstream = socket.create_connection((normalized_host, port), timeout=30)
        except OSError as exc:
            emit("upstream_error", host=normalized_host, port=port, error=str(exc))
            self.request.sendall(b"HTTP/1.1 502 Bad Gateway\r\nConnection: close\r\n\r\n")
            return

        emit("allowed", host=normalized_host, port=port, client=self.client_address[0])
        self.request.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        try:
            relay(self.request, upstream)
        finally:
            upstream.close()


class Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


emit("ready", port=PORT, allowed_hosts=ALLOWED_HOSTS)
with Server(("0.0.0.0", PORT), Handler) as server:
    server.serve_forever()
'''


def _docker_env_value(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        return "<unset>"
    if value == "":
        return "<empty>"
    return value


def _describe_docker_exception(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def _is_wait_timeout_exception(exc: Exception) -> bool:
    if isinstance(exc, requests_exceptions.ReadTimeout):
        return True
    if not isinstance(exc, requests_exceptions.ConnectionError):
        return False

    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None:
        if id(current) in seen:
            break
        seen.add(id(current))
        if isinstance(current, (TimeoutError, socket.timeout, urllib3_exceptions.ReadTimeoutError)):
            return True
        current = current.__cause__ or current.__context__
    return False


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
    egress_allowlist: list[str] = field(default_factory=list[str])
    tty: bool = False


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
        self._egress_proxy: Container | None = None
        self._isolated_network: Network | None = None

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
        environment = dict(config.environment)
        network_mode = config.network_mode
        dns: list[str] | None = None

        try:
            if config.egress_allowlist:
                network_mode, proxy_ip = self._create_restricted_egress(
                    config.image,
                    config.egress_allowlist,
                )
                proxy_url = f"http://{proxy_ip}:{EGRESS_PROXY_PORT}"
                environment.update(
                    {
                        "HTTP_PROXY": proxy_url,
                        "HTTPS_PROXY": proxy_url,
                        "ALL_PROXY": proxy_url,
                        "http_proxy": proxy_url,
                        "https_proxy": proxy_url,
                        "all_proxy": proxy_url,
                        "NO_PROXY": "localhost,127.0.0.1",
                        "no_proxy": "localhost,127.0.0.1",
                    }
                )
                # The proxy receives hostnames and performs DNS resolution on
                # the egress network. The agent itself needs no DNS service.
                dns = ["127.0.0.1"]

            container: Container = self._client.containers.create(
                image=config.image,
                command=config.command,
                environment=environment,
                volumes=config.volumes or None,
                mem_limit=config.mem_limit,
                nano_cpus=config.cpu_count * 10**9,
                network_mode=network_mode,
                dns=dns,
                working_dir=str(CONTAINER_WORKSPACE),
                tty=config.tty,
                detach=True,
            )
        except Exception:
            self._cleanup_restricted_egress()
            raise
        self._container = container
        log.info("Created container %s (image=%s)", container.short_id, config.image)
        return str(container.id)

    def _create_restricted_egress(
        self,
        image: str,
        allowed_hosts: list[str],
    ) -> tuple[str, str]:
        """Create an internal network plus a host-allowlisting CONNECT proxy."""
        normalized_hosts = sorted({host.rstrip(".").lower() for host in allowed_hosts})
        invalid_host = any("/" in host or ":" in host for host in normalized_hosts)
        if not all(normalized_hosts) or invalid_host:
            raise ValueError("egress_allowlist entries must be DNS hostnames without ports")

        network_name = f"clispecbench-isolated-{uuid.uuid4().hex[:12]}"
        network = self._client.networks.create(
            network_name,
            driver="bridge",
            internal=True,
            labels={"clispecbench.network-policy": "api-only"},
        )
        self._isolated_network = network

        proxy: Container = self._client.containers.create(
            image=image,
            command=[
                "python3",
                "-u",
                "-c",
                _EGRESS_PROXY_SOURCE,
                str(EGRESS_PROXY_PORT),
                json.dumps(normalized_hosts),
            ],
            network_mode="bridge",
            mem_limit="128m",
            nano_cpus=10**9,
            working_dir="/tmp",
            detach=True,
            labels={"clispecbench.component": "egress-proxy"},
        )
        self._egress_proxy = proxy
        network.connect(proxy)  # pyright: ignore[reportUnknownMemberType]
        proxy.start()
        proxy.reload()
        network_settings = proxy.attrs["NetworkSettings"]["Networks"][network_name]
        proxy_ip = str(network_settings["IPAddress"])
        if not proxy_ip:
            raise RuntimeError("Restricted-egress proxy did not receive an internal address")

        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            proxy.reload()
            if proxy.status == "exited":
                audit = self.get_network_audit_logs()
                raise RuntimeError(f"Restricted-egress proxy exited: {audit}")
            if '"event": "ready"' in self.get_network_audit_logs():
                log.info(
                    "Created restricted network %s (allowed hosts: %s)",
                    network_name,
                    ", ".join(normalized_hosts),
                )
                return network_name, proxy_ip
            time.sleep(0.05)
        raise RuntimeError("Restricted-egress proxy did not become ready")

    def copy_in(self, host_path: Path, container_path: PurePosixPath) -> None:
        """Copy a file or directory from the host into the container.

        Intermediate directories under ``/tmp`` are created automatically:
        when ``container_path`` descends into ``/tmp`` we tar with a
        ``/tmp``-relative arcname and extract at ``/tmp`` so tar itself
        materializes any parents. Non-``/tmp`` destinations fall back to
        extracting at ``container_path.parent``, which must already exist.
        """
        if self._container is None:
            raise RuntimeError("No container created")
        import io
        import tarfile

        tmp = PurePosixPath("/tmp")
        try:
            rel_to_tmp = container_path.relative_to(tmp)
        except ValueError:
            extract_at = str(container_path.parent)
            arcname = container_path.name
        else:
            extract_at = str(tmp)
            arcname = str(rel_to_tmp)

        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            tar.add(str(host_path), arcname=arcname)
        buf.seek(0)
        self._container.put_archive(extract_at, buf)  # pyright: ignore[reportUnknownMemberType]

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
        except Exception as exc:
            if not _is_wait_timeout_exception(exc):
                log.warning(
                    "Unexpected Docker wait exception for container %s: %s",
                    self._container.short_id,
                    _describe_docker_exception(exc),
                )
                raise

            # SDK wait timeout — kill the container and report a timeout.
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
        """Remove the agent container and its per-run network resources."""
        if self._container is not None:
            try:
                self._container.remove(force=True)
                log.info("Removed container %s", self._container.short_id)
            except docker.errors.NotFound:
                pass
            self._container = None
        self._cleanup_restricted_egress()

    def _cleanup_restricted_egress(self) -> None:
        if self._egress_proxy is not None:
            try:
                self._egress_proxy.remove(force=True)
                log.info("Removed egress proxy %s", self._egress_proxy.short_id)
            except docker.errors.NotFound:
                pass
            finally:
                self._egress_proxy = None
        if self._isolated_network is not None:
            try:
                self._isolated_network.remove()
                log.info("Removed isolated Docker network")
            except docker.errors.NotFound:
                pass
            finally:
                self._isolated_network = None

    def get_logs(self) -> str:
        """Return stdout + stderr logs from the container."""
        if self._container is None:
            raise RuntimeError("No container created")
        raw: bytes = self._container.logs()
        return raw.decode("utf-8", errors="replace")

    def get_network_audit_logs(self) -> str:
        """Return JSONL connection decisions from the restricted-egress proxy."""
        if self._egress_proxy is None:
            return ""
        raw: bytes = self._egress_proxy.logs()
        return raw.decode("utf-8", errors="replace")

    def run_oneshot(
        self,
        config: ContainerConfig,
        timeout_seconds: float,
    ) -> tuple[int | None, str]:
        """Create, start, wait, and return (exit_code, logs) for a one-shot container.

        The container is removed after use regardless of outcome.
        """
        prev = (self._container, self._egress_proxy, self._isolated_network)
        self._container = None
        self._egress_proxy = None
        self._isolated_network = None
        try:
            self.create(config)
            run = self.start_and_wait(timeout_seconds)
            logs = self.get_logs()
            return run.exit_code, logs
        finally:
            if self._container is not None:
                self.cleanup()
            self._container, self._egress_proxy, self._isolated_network = prev
