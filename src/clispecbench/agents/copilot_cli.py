"""Agent adapter for GitHub Copilot CLI."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, cast

from clispecbench.agents.base import AgentAdapter, read_dockerfile_arg
from clispecbench.harness.results import TokenUsage

log = logging.getLogger(__name__)

DOCKERFILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "docker" / "agents" / "copilot-cli.Dockerfile"
)

# Path inside the container where OTel data is written as JSON-lines
OTEL_FILE_PATH = "/tmp/copilot-otel.jsonl"


class CopilotCLIAdapter(AgentAdapter):
    """Adapter for GitHub Copilot CLI (``copilot``)."""

    def __init__(
        self,
        model: str | None = None,
        effort: str | None = None,
    ) -> None:
        self._model = model
        self._effort = effort

    @property
    def name(self) -> str:
        return "copilot-cli"

    @property
    def version(self) -> str:
        return read_dockerfile_arg(DOCKERFILE, "COPILOT_CLI_VERSION")

    @property
    def dockerfile(self) -> Path:
        return DOCKERFILE

    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        env = {**api_key_env}
        # Auto-discover GitHub token if not explicitly provided.
        # Copilot CLI checks COPILOT_GITHUB_TOKEN, GH_TOKEN, GITHUB_TOKEN
        # (in that order).  We try `gh auth token` and common env vars.
        token_vars = ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")
        if not any(v in env for v in token_vars):
            token = _discover_gh_token()
            if token:
                env["COPILOT_GITHUB_TOKEN"] = token
            else:
                log.warning(
                    "No GitHub token found. Set COPILOT_GITHUB_TOKEN, "
                    "GH_TOKEN, or run 'gh auth login'."
                )
        # Enable OTel file export for token tracking. `setdefault` keeps any
        # user-provided values while still enabling a default export path.
        # COPILOT_OTEL_ENABLED activates instrumentation (available since
        # v1.0.4).  COPILOT_OTEL_FILE_EXPORTER_PATH tells the CLI to write
        # metrics/traces as JSON-lines to a local file instead of requiring
        # an OTLP endpoint.
        env.setdefault("COPILOT_OTEL_ENABLED", "true")
        env.setdefault("COPILOT_OTEL_FILE_EXPORTER_PATH", OTEL_FILE_PATH)
        env.setdefault("COPILOT_OTEL_EXPORTER_TYPE", "file")
        return env

    @property
    def model(self) -> str | None:
        return self._model

    @property
    def effort(self) -> str | None:
        return self._effort

    def invoke_command(
        self, prompt_path: PurePosixPath, work_dir: PurePosixPath,
    ) -> list[str]:
        # Copilot CLI's -p flag takes a literal text argument (not stdin),
        # so we use command substitution to read the prompt file.
        flags = "--yolo --output-format json --no-auto-update"
        if self._model:
            flags += f' --model "{self._model}"'
        if self._effort:
            flags += f' --effort "{self._effort}"'
        return [
            "bash", "-c",
            f'cd "{work_dir}" && copilot -p "$(cat {prompt_path})" {flags}',
        ]

    def parse_token_usage(
        self,
        container_fs: Path,
        container_logs: str = "",
    ) -> TokenUsage | None:
        """Parse token usage from OTel file export or JSONL output.

        OTel is preferred because it reports both input and output tokens,
        while the JSONL event stream only has output tokens.
        """
        # copy_out() extracts /tmp/copilot-otel.jsonl to extract_dir/copilot-otel.jsonl
        otel_file = container_fs / "copilot-otel.jsonl"
        log.debug("Looking for OTel file at %s (exists=%s)", otel_file, otel_file.is_file())
        if otel_file.is_file():
            otel_usage = _parse_otel_file(otel_file)
            if otel_usage is not None:
                # Supplement with tool call count from JSONL
                otel_usage.tool_calls = _count_tool_calls(container_logs)
                return otel_usage

        # Fall back to JSONL output (only has output tokens)
        usage = _parse_jsonl_usage(container_logs)
        if usage is not None:
            return usage

        log.info("No token usage found in Copilot CLI output")
        return None

    def credential_mounts(self, host_home: Path) -> dict[str, dict[str, str]]:
        # Copilot CLI authenticates via COPILOT_GITHUB_TOKEN / GH_TOKEN env
        # var, so credential file mounts are not strictly needed.  However,
        # we mount the gh hosts.yml so the CLI can discover the token if the
        # caller sets up the env var via the harness's api_key_env dict.
        gh_hosts = host_home / ".config" / "gh" / "hosts.yml"
        appdata_hosts = host_home / "AppData" / "Roaming" / "GitHub CLI" / "hosts.yml"
        mounts: dict[str, dict[str, str]] = {}
        # Try AppData location first (Windows), then XDG (Linux/WSL)
        for src in (appdata_hosts, gh_hosts):
            if src.exists():
                mounts[src.as_posix()] = {
                    "bind": "/root/.config/gh/hosts.yml",
                    "mode": "ro",
                }
                break
        return mounts

    @property
    def telemetry_paths(self) -> list[str]:
        return [OTEL_FILE_PATH]

    @property
    def allowed_hosts(self) -> list[str]:
        return [
            "api.github.com",
            "api.individual.githubcopilot.com",
            "copilot-proxy.githubusercontent.com",
        ]

    def extract_last_agent_message(self, container_logs: str) -> str | None:
        """Extract last assistant.message text from Copilot CLI JSONL output."""
        for line in reversed(container_logs.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if event.get("type") != "assistant.message":
                continue
            data = event.get("data", event)
            text = data.get("text", data.get("content", ""))
            if isinstance(text, str) and text.strip():
                return text
        return None


def _parse_jsonl_usage(container_logs: str) -> TokenUsage | None:
    """Parse token usage from the Copilot CLI JSON output.

    The ``--output-format json`` flag emits JSONL events.  Token counts
    come from two places:

    - ``assistant.message`` events carry an ``outputTokens`` field.
    - The final ``result`` event carries ``usage`` with session-level
      stats (``premiumRequests``, ``totalApiDurationMs``, etc.) but may
      also contain ``input_tokens`` / ``output_tokens`` in future versions.

    We sum ``outputTokens`` from assistant messages and check the result
    event for any token-level data.
    """
    output_tokens = 0
    input_tokens = 0
    cache_read_tokens = 0
    cache_creation_tokens = 0
    result_found = False

    for line in container_logs.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        event_type = event.get("type", "")

        if event_type == "assistant.message":
            data = event.get("data", event)
            output_tokens += int(data.get("outputTokens", 0))

        elif event_type == "result":
            result_found = True
            raw_usage = event.get("usage", {})
            if isinstance(raw_usage, dict):
                usage = cast(dict[str, Any], raw_usage)
                input_tokens += int(usage.get("input_tokens", 0))
                output_tokens += int(usage.get("output_tokens", 0))
                # Keep this permissive for evolving Copilot result schemas.
                cache_read_tokens += int(
                    usage.get("cache_read_input_tokens")
                    or usage.get("cached_input_tokens")
                    or usage.get("cache_read_tokens")
                    or 0
                )
                cache_creation_tokens += int(
                    usage.get("cache_creation_input_tokens")
                    or usage.get("cache_write_input_tokens")
                    or 0
                )
    if not result_found:
        return None

    if input_tokens == 0 and output_tokens == 0:
        return None

    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=cache_read_tokens or None,
        cache_creation_input_tokens=cache_creation_tokens or None,
        tool_calls=_count_tool_calls(container_logs),
        # Intentionally unset for Copilot CLI:
        # `github.copilot.cost` is not treated as API-USD here.
        reported_cost_usd=None,
    )


def _count_tool_calls(container_logs: str) -> int:
    """Count tool invocations in Copilot CLI JSONL event stream.

    Copilot has emitted multiple JSON output schemas:

    - older: ``{"type":"tool_call", ...}``
    - newer: ``tool.execution_start`` / ``tool.execution_complete`` with
      ``data.toolCallId``.
    """
    count_legacy = 0
    call_ids: set[str] = set()
    for line in container_logs.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        event_type = event.get("type")
        if event_type == "tool_call":
            count_legacy += 1
            continue
        if event_type not in {"tool.execution_start", "tool.execution_complete"}:
            continue
        raw_data = event.get("data")
        if not isinstance(raw_data, dict):
            continue
        data = cast(dict[str, Any], raw_data)
        tool_call_id = data.get("toolCallId")
        if isinstance(tool_call_id, str) and tool_call_id:
            call_ids.add(tool_call_id)
    return max(count_legacy, len(call_ids))


def _parse_otel_file(otel_file: Path) -> TokenUsage | None:
    """Parse token usage from the Copilot CLI OTel JSON-lines file.

    The CLI writes flat JSONL records (not OTLP-wrapped ``resourceMetrics``).
    Token data comes from ``gen_ai.client.token.usage`` metric entries whose
    ``dataPoints`` carry cumulative histogram values.  The file may contain
    multiple snapshots; we take the last one (highest cumulative totals).
    """
    metric_input_tokens = 0
    metric_output_tokens = 0
    metric_tool_calls = 0
    span_tool_calls = 0

    chat_input_tokens = 0
    chat_output_tokens = 0
    chat_cache_read_tokens = 0
    chat_cache_creation_tokens = 0
    invoke_input_tokens: int | None = None
    invoke_output_tokens: int | None = None
    invoke_cache_read_tokens: int | None = None
    invoke_cache_creation_tokens: int | None = None

    try:
        for line in otel_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record: Any = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue

            for span in _extract_otel_spans(record):
                attrs = _normalize_otel_attributes(span.get("attributes", {}))
                operation = str(attrs.get("gen_ai.operation.name", ""))
                if operation == "execute_tool":
                    span_tool_calls += 1
                    continue
                if operation == "chat":
                    chat_input_tokens += _coerce_int(attrs.get("gen_ai.usage.input_tokens")) or 0
                    chat_output_tokens += _coerce_int(attrs.get("gen_ai.usage.output_tokens")) or 0
                    chat_cache_read_tokens += (
                        _coerce_int(attrs.get("gen_ai.usage.cache_read.input_tokens")) or 0
                    )
                    chat_cache_creation_tokens += (
                        _coerce_int(attrs.get("gen_ai.usage.cache_creation.input_tokens")) or 0
                    )
                    continue
                if operation == "invoke_agent":
                    invoke_input_tokens = _coerce_int(attrs.get("gen_ai.usage.input_tokens"))
                    invoke_output_tokens = _coerce_int(attrs.get("gen_ai.usage.output_tokens"))
                    invoke_cache_read_tokens = _coerce_int(
                        attrs.get("gen_ai.usage.cache_read.input_tokens")
                    )
                    invoke_cache_creation_tokens = _coerce_int(
                        attrs.get("gen_ai.usage.cache_creation.input_tokens")
                    )

            for metric in _extract_otel_metrics(record):
                metric_name = str(metric.get("name", ""))
                if metric_name == "gen_ai.client.token.usage":
                    for dp in metric.get("dataPoints", []):
                        attrs = _normalize_otel_attributes(dp.get("attributes", {}))
                        token_type = str(attrs.get("gen_ai.token.type", ""))
                        # Value may be a histogram dict ({"sum": N, ...}) or a scalar
                        value = _metric_value(dp.get("value", 0))
                        # Cumulative — last entry wins
                        if token_type == "input":
                            metric_input_tokens = value
                        elif token_type == "output":
                            metric_output_tokens = value
                    continue

                if metric_name == "github.copilot.tool.call.count":
                    snapshot_calls = 0
                    for dp in metric.get("dataPoints", []):
                        typed_dp = cast(dict[str, Any], dp)
                        snapshot_calls += _metric_value(typed_dp.get("value", 0))
                    metric_tool_calls = max(metric_tool_calls, snapshot_calls)
    except (OSError, TypeError, AttributeError):
        log.warning("Failed to parse OTel file %s", otel_file, exc_info=True)

    # Prefer invoke_agent totals when present. They include full-session
    # cumulative counters and avoid ambiguity around incremental snapshots.
    if invoke_input_tokens is not None or invoke_output_tokens is not None:
        input_tokens = invoke_input_tokens or 0
        output_tokens = invoke_output_tokens or 0
    elif metric_input_tokens > 0 or metric_output_tokens > 0:
        input_tokens = metric_input_tokens
        output_tokens = metric_output_tokens
    else:
        input_tokens = chat_input_tokens
        output_tokens = chat_output_tokens

    if invoke_cache_read_tokens is not None:
        cache_read_tokens = invoke_cache_read_tokens
    else:
        cache_read_tokens = chat_cache_read_tokens

    if invoke_cache_creation_tokens is not None:
        cache_creation_tokens = invoke_cache_creation_tokens
    else:
        cache_creation_tokens = chat_cache_creation_tokens

    if metric_tool_calls > 0:
        tool_calls = metric_tool_calls
    elif span_tool_calls > 0:
        tool_calls = span_tool_calls
    else:
        tool_calls = None

    if (
        input_tokens == 0
        and output_tokens == 0
        and (cache_read_tokens or 0) == 0
        and (cache_creation_tokens or 0) == 0
    ):
        return None
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=cache_read_tokens or None,
        cache_creation_input_tokens=cache_creation_tokens or None,
        tool_calls=tool_calls,
        # Intentionally unset for Copilot CLI:
        # `github.copilot.cost` is a Copilot-side usage/billing unit and does
        # not map cleanly to OpenAI API USD in this harness. We only report the
        # comparable `estimated_cost_usd` derived from token counts + pricing.py.
        reported_cost_usd=None,
    )


def _normalize_otel_attributes(attributes: Any) -> dict[str, Any]:
    """Normalize OTel attributes into a dict.

    The file exporter in some versions returns attributes as a dict, while
    others return OpenTelemetry-style key-value arrays.
    """
    if isinstance(attributes, dict):
        typed_attributes = cast(dict[str, Any], attributes)
        return {str(k): v for k, v in typed_attributes.items()}
    if isinstance(attributes, list):
        normalized: dict[str, Any] = {}
        typed_attributes = cast(list[Any], attributes)
        for raw_attr in typed_attributes:
            if not isinstance(raw_attr, dict):
                continue
            attr = cast(dict[str, Any], raw_attr)
            key = attr.get("key")
            value = attr.get("value")
            if key is not None:
                normalized[str(key)] = _normalize_otel_value(value)
        return normalized
    return {}


def _normalize_otel_value(value: Any) -> Any:
    """Normalize typed OTEL values into plain Python scalars/containers."""
    if not isinstance(value, dict):
        return value
    typed_value = cast(dict[str, Any], value)
    if "stringValue" in typed_value:
        return typed_value.get("stringValue")
    if "intValue" in typed_value:
        return _coerce_int(typed_value.get("intValue"))
    if "doubleValue" in typed_value:
        return _coerce_float(typed_value.get("doubleValue"))
    if "boolValue" in typed_value:
        return bool(typed_value.get("boolValue"))
    if "arrayValue" in typed_value:
        array_value = typed_value.get("arrayValue")
        raw_values: Any = []
        if isinstance(array_value, dict):
            array_value_d = cast(dict[str, Any], array_value)
            raw_values = array_value_d.get("values", [])
        if isinstance(raw_values, list):
            typed_values = cast(list[Any], raw_values)
            return [_normalize_otel_value(v) for v in typed_values]
    return typed_value


def _extract_otel_metrics(record: Any) -> list[dict[str, Any]]:
    """Return metric objects from either flat and nested OTel JSON shapes."""
    metrics: list[dict[str, Any]] = []
    if not isinstance(record, dict):
        return metrics
    record_d = cast(dict[str, Any], record)

    # Flat JSON lines for copilot OTel file export
    if record_d.get("type") == "metric" and isinstance(record_d.get("dataPoints"), list):
        metrics.append(record_d)

    # OTLP-style resource metrics payload
    resource_metrics = record_d.get("resourceMetrics")
    if isinstance(resource_metrics, list):
        for rm_raw in cast(list[Any], resource_metrics):
            if not isinstance(rm_raw, dict):
                continue
            rm = cast(dict[str, Any], rm_raw)
            scope_metrics = rm.get("scopeMetrics")
            if not isinstance(scope_metrics, list):
                continue
            for sm_raw in cast(list[Any], scope_metrics):
                if not isinstance(sm_raw, dict):
                    continue
                sm = cast(dict[str, Any], sm_raw)
                nested_metrics = sm.get("metrics")
                if not isinstance(nested_metrics, list):
                    continue
                for m_raw in cast(list[Any], nested_metrics):
                    if isinstance(m_raw, dict):
                        metrics.append(cast(dict[str, Any], m_raw))

    # Copilot sometimes nests the metric directly under an event name.
    for wrapped in (
        "metric",
        "otelMetric",
        "metrics",
    ):
        payload = record_d.get(wrapped)
        if isinstance(payload, list):
            payload_list = cast(list[Any], payload)
            metrics.extend(
                [cast(dict[str, Any], m) for m in payload_list if isinstance(m, dict)]
            )
    return metrics


def _extract_otel_spans(record: Any) -> list[dict[str, Any]]:
    """Return span objects from flat and nested OTel JSON shapes."""
    spans: list[dict[str, Any]] = []
    if not isinstance(record, dict):
        return spans
    record_d = cast(dict[str, Any], record)

    if record_d.get("type") == "span" and isinstance(record_d.get("attributes"), dict):
        spans.append(record_d)

    resource_spans = record_d.get("resourceSpans")
    if isinstance(resource_spans, list):
        for rs_raw in cast(list[Any], resource_spans):
            if not isinstance(rs_raw, dict):
                continue
            rs = cast(dict[str, Any], rs_raw)
            scope_spans = rs.get("scopeSpans")
            if not isinstance(scope_spans, list):
                continue
            for ss_raw in cast(list[Any], scope_spans):
                if not isinstance(ss_raw, dict):
                    continue
                ss = cast(dict[str, Any], ss_raw)
                nested_spans = ss.get("spans")
                if not isinstance(nested_spans, list):
                    continue
                for span_raw in cast(list[Any], nested_spans):
                    if isinstance(span_raw, dict):
                        spans.append(cast(dict[str, Any], span_raw))

    for wrapped in (
        "span",
        "otelSpan",
        "spans",
    ):
        payload = record_d.get(wrapped)
        if isinstance(payload, dict):
            spans.append(cast(dict[str, Any], payload))
        elif isinstance(payload, list):
            payload_list = cast(list[Any], payload)
            spans.extend(
                [cast(dict[str, Any], s) for s in payload_list if isinstance(s, dict)]
            )
    return spans


def _metric_value(raw_value: Any) -> int:
    """Extract a numeric value from OTEL metric datapoint values."""
    if isinstance(raw_value, dict):
        typed_value = cast(dict[str, Any], raw_value)
        for key in ("sum", "asInt", "asDouble"):
            value = _coerce_int(typed_value.get(key))
            if value is not None:
                return value
        return 0
    value = _coerce_int(raw_value)
    return value if value is not None else 0


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return None
        try:
            return int(v)
        except ValueError:
            try:
                return int(float(v))
            except ValueError:
                return None
    return None


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return None
        try:
            return float(v)
        except ValueError:
            return None
    return None


def _discover_gh_token() -> str | None:
    """Try to discover a GitHub token from the environment or ``gh`` CLI."""
    for var in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        value = os.environ.get(var)
        if value:
            return value
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=10,
        )
        token = result.stdout.strip()
        if result.returncode == 0 and token:
            return token
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None
