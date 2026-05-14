# CLISpecBench Evaluation Harness — Design Document

**Author:** Matthew G. Knutson
**Status:** Living design document
**Last Updated:** May 2026

---

> **Note on task IDs.** The harness exposes explicit language task IDs such as
> `rs274-cpp`, `iges-js`, and `marc21-rs`. Registered evals currently include
> BibTeX, GEDCOM, ICal, IGES, LAS, MARC21, RS274, and WordCount. Task IDs use
> the `<eval>-<language>` shape and are resolved from the eval registry plus
> the shared language-requirements prompts in `Evals/_shared/`.

## 1. Purpose

This document describes the evaluation harness: the software that invokes AI
coding agents against CLISpecBench tasks, captures their output, builds it,
runs the pytest scoring suite, and records structured results.

It is a companion to `Eval-Design.md`, which defines the benchmark's
scoring model and task anatomy. This document covers the harness
implementation: how those concepts become running code.

---

## 2. Goals

1. **Run any supported agent against any task with a single command.**
   `clispecbench run --task rs274-cpp --agent claude-code`

2. **Produce structured, machine-readable results** that capture per-test
   pass/fail, token usage, timing, and scoring — enabling cross-model and
   cross-task analysis.

3. **Sandbox agent execution** so that agents cannot affect the host and the
   network condition for a run series is explicit and reproducible. The current
   published study preserves the historical effective access level documented
   in `Agent-Run-Notes.md`; future API-only/offline runs must be labeled as a
   separate condition.

4. **Be agent-agnostic.** Adding a new agent CLI should require only a small
   adapter module, not changes to the core harness.

---

## 3. Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│  clispecbench CLI                                  │
│                                                      │
│  run --task <id> --agent <name> [--runs N] ...       │
└──────────┬───────────────────────────────────────────┘
           │
           ▼
┌──────────────────────┐     ┌──────────────────────┐
│  Task Registry       │     │  Agent Registry       │
│                      │     │                       │
│  Resolves eval +     │     │  Selects adapter for  │
│  language task IDs   │     │  the named agent      │
└──────────┬───────────┘     └──────────┬────────────┘
           │                            │
           ▼                            ▼
┌──────────────────────────────────────────────────────┐
│  Runner (orchestrates one eval run)                  │
│                                                      │
│  1. Prepare workspace (assembled prompt + docs)      │
│  2. Build & start Docker container                   │
│  3. Invoke agent via adapter                         │
│  4. Wait for completion or timeout                   │
│  5. Extract workspace from container                 │
│  6. Prepare submission via language backend          │
│  7. Run pytest suite (pytest --json-report)          │
│  8. Compute scores and capability breakdowns         │
│  9. Collect token/cost metadata from adapter         │
│  10. Preserve transcript + source artifacts          │
│  11. Write structured result JSON                    │
└──────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────┐
│  Results (one JSON file per run)                     │
│                                                      │
│  transient_results/<task>/<agent>/<run>.json         │
└──────────────────────────────────────────────────────┘
```

---

## 4. Directory Layout

```
src/clispecbench/
  __init__.py
  cli.py                        # CLI entry point (clispecbench command)
  pytest_plugin.py              # Shared pytest fixtures for eval suites

  harness/
    __init__.py
    runner.py                   # Orchestrates a single eval run end-to-end
    docker.py                   # Container lifecycle management
    task.py                     # Task registry: loads prompts, tests
    workspace.py                # Prepares the clean working directory for the agent
    scoring.py                  # Correctness, coverage, quality scoring
    results.py                  # Result schema, serialization, aggregation
    publish.py                  # Publish transient runs to published_results/
    pricing.py                  # Cost estimation from normalized token counts

  agents/
    __init__.py
    base.py                     # Abstract AgentAdapter interface
    registry.py                 # Supported agent registry and Docker image metadata
    claude_code.py              # Claude Code CLI adapter
    codex_cli.py                # Codex CLI adapter
    copilot_cli.py              # GitHub Copilot CLI adapter
    gemini_cli.py               # Gemini CLI adapter
    opencode.py                 # OpenCode adapter
    openhands_cli.py            # OpenHands CLI adapter

  build/
    backends.py                 # C++, Python, JavaScript, and Rust backends
    build.py                    # CMake command helpers
    target.py                   # ImplementationTarget, find_repo_root

Evals/
  _shared/                          # Shared across evals
    language-requirements-cpp.md        # C++ boilerplate
    language-requirements-py.md         # Python boilerplate
    language-requirements-js.md         # JavaScript boilerplate
    language-requirements-rs.md         # Rust boilerplate
  RS274/                           # CNC G-code interpreter eval
    prompt/
      base-prompt.md
      technical-requirements-prompt.md
      docs/
    tests/
      rs274_support.py                 # RS274 test helpers
      rs274_parameters.py              # RS274 parameter constants
      modal_groups.py                  # RS274 modal group constants
    reference-implementation-cpp/       # C++ reference
    reference-implementation-py/        # Python reference
    reference-implementation-js/        # JavaScript reference
  BibTeX/ GEDCOM/ ICal/ IGES/ LAS/ MARC21/ WordCount/
    prompt/ tests/ reference-implementation-<lang>/

docker/
  base.Dockerfile               # C++/Python/Node/Rust toolchains + pytest
  agents/
    claude-code.Dockerfile      # Extends base, installs Claude Code CLI
    codex-cli.Dockerfile        # Extends base, installs Codex CLI
    copilot-cli.Dockerfile      # Extends base, installs Copilot CLI
    gemini-cli.Dockerfile       # Extends base, installs Gemini CLI
    opencode.Dockerfile         # Extends base, installs OpenCode
    openhands.Dockerfile        # Extends base, installs OpenHands

scripts/
  install-docker-wsl.sh         # Docker Engine install in WSL2 Ubuntu
  smoke-test-*.sh               # Verify CLI auth works inside containers
  _queue-template.sh            # Local ignored one-off queue script template
```

---

## 5. Agent Adapter Interface

Each supported agent implements this interface. The harness interacts with
agents only through this abstraction.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass
class TokenUsage:
    """Normalized token usage from any agent."""
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int | None = None
    cache_creation_input_tokens: int | None = None
    tool_calls: int | None = None
    reported_cost_usd: float | None = None
    estimated_cost_usd: float | None = None
    cost_estimate_blocked_reason: str | None = None
    source: str | None = None
    is_partial: bool = False


@dataclass
class AgentRunResult:
    """What the adapter returns after an agent run completes."""
    exit_reason: str              # "completed" | "timeout" | "token_limit" | "error"
    wall_clock_seconds: float
    token_usage: TokenUsage | None
    raw_log_path: Path | None     # Agent-specific log (for debugging, not scoring)
    error_message: str | None = None


class AgentAdapter(ABC):
    """Abstract base for all agent adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent identifier used in results and CLI (e.g., "claude-code")."""

    @property
    def version(self) -> str:
        """Agent CLI version string."""
        return "unknown"

    @property
    @abstractmethod
    def dockerfile(self) -> Path:
        """Path to the Dockerfile that builds this agent's container image."""

    @abstractmethod
    def environment(self, api_key_env: dict[str, str]) -> dict[str, str]:
        """Environment variables to inject into the container.

        api_key_env contains the user-provided secrets (e.g., ANTHROPIC_API_KEY).
        The adapter adds any agent-specific env vars and returns the merged dict.
        """

    @abstractmethod
    def invoke_command(
        self,
        prompt_path: PurePosixPath,
        work_dir: PurePosixPath,
    ) -> list[str]:
        """The shell command to start the agent inside the container.

        prompt_path: path (inside the container) to the assembled prompt file.
        work_dir: path (inside the container) to the clean working directory.
        Returns: command + args as a list of strings.
        """

    @abstractmethod
    def parse_token_usage(
        self,
        container_fs: Path,
        container_logs: str = "",
    ) -> TokenUsage | None:
        """Extract token usage from agent-specific logs or telemetry.

        container_fs: root of the extracted container filesystem.
        container_logs: stdout/stderr captured from the container.
        Returns: normalized TokenUsage, or None if unavailable.
        """

    def credential_mounts(self, host_home: Path) -> dict[str, dict[str, str]]:
        """Return Docker volume mounts for agent credentials."""
        return {}

    @property
    def telemetry_paths(self) -> list[str]:
        """Container paths to extract before token usage parsing."""
        return []

    @property
    def canonical_transcript_container_dir(self) -> str | None:
        """Container directory holding the agent CLI's own transcript, if any."""
        return None

    @property
    def allowed_hosts(self) -> list[str]:
        """Declared API hosts for future restricted-network run series."""
        return []
```

### 5.1 Adapter Implementation Notes

**Claude Code.** Invoked via `claude --print` with `--output-format stream-json`.
Token usage is parsed from the terminal stream's final `result` event. The
adapter also configures OpenTelemetry file export under `/tmp/otel` as a
fallback and parses the `claude_code.token.usage` metric when stream usage is
missing.

**Codex CLI.** Invoked via `codex exec --json`. Token usage is parsed first
from the JSONL event stream — `turn.completed` events contain `input_tokens`,
`cached_input_tokens`, and `output_tokens`. If the run ends with `turn.failed`,
the event stream does not carry a final usage object, so the adapter falls back
to Codex's persisted session rollouts under `/root/.codex/sessions/` and reads
the latest `token_count.info.total_token_usage` snapshot. That fallback is
marked `is_partial: true` because it is authoritative only through the last
model response for which Codex received `response.completed`; it cannot include
tokens from a provider stream that failed before completion.

**Gemini CLI.** Invoked in non-interactive mode with stream-JSON output. Token
usage is parsed from the final `result` event's `stats` object when Gemini emits
one.

**Copilot CLI.** Invoked through the Copilot CLI adapter and authenticated via
the host Copilot credentials mounted by `scripts/smoke-test-copilot.sh`.

**OpenCode.** Invoked through the OpenCode adapter. The current smoke-tested
path uses OpenRouter credentials for external model access.

**OpenHands.** Invoked through the OpenHands CLI adapter. OpenRouter-backed
models are configured through the adapter environment and verified by
`scripts/smoke-test-openhands.sh`.

---

## 6. Docker Sandbox

### 6.1 Container Design

Each agent run executes in an isolated Docker container. The base image
provides the task's required toolchain. Agent-specific images extend the
base with the agent CLI.

```dockerfile
# docker/base.Dockerfile
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    build-essential cmake g++-14 python3 python3-pip \
    python3-venv git ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22 and stable Rust are installed in the real base image for
# JavaScript and Rust language variants.

# Pin compiler version for reproducibility
ENV CC=gcc-14 CXX=g++-14

WORKDIR /workspace
```

```dockerfile
# docker/agents/claude-code.Dockerfile
FROM clispecbench-base:latest

RUN npm install -g @anthropic-ai/claude-code@<pinned-version>

# Directory used by Claude Code's OpenTelemetry file export fallback
RUN mkdir -p /tmp/otel
```

### 6.2 Authentication

Agent CLIs authenticate via OAuth tokens stored on the host machine. The
harness mounts host credential files into the container at runtime. Each
agent has different requirements (verified via smoke testing):

| Agent | Host files | Mount strategy |
|-------|-----------|----------------|
| Claude Code | `~/.claude/.credentials.json` (read-only), `~/.claude/settings.json` (read-only) | Mount the two files individually `:ro` |
| Codex CLI | `~/.codex/auth.json` (read/write, file only) | Mount single file `:rw`; rest of `.codex/` stays writable |
| Gemini CLI | `~/.gemini/oauth_creds.json`, `google_accounts.json`, `settings.json` | Copy to writable dir at startup; seed `projects.json` |
| Copilot CLI | Host Copilot auth files | See `scripts/smoke-test-copilot.sh` |
| OpenCode | `OPENROUTER_API_KEY` or provider-specific env | Inject via environment; see `scripts/smoke-test-opencode.sh` |
| OpenHands | `OPENROUTER_API_KEY` or provider-specific env | Inject via environment; see `scripts/smoke-test-openhands.sh` |

Notes:
- Claude Code: `~/.claude.json` is deliberately **not** mounted. That host
  file caches the user's claude.ai connector registrations (Gmail / GCal /
  Drive MCP servers under `claudeAiMcpEverConnected`); mounting it leaked
  those connector names into the in-container session's `tools` list and
  `mcp_servers` advertisement, contaminating eval runs. Verified empirically
  that the CLI runs cleanly without the file (claude-code 2.1.120) — no
  warnings on stdout/stderr, `mcp_servers:[]`, no `mcp__*` tools advertised.
- Mounting `~/.claude/` as a directory is also avoided: the CLI needs to
  create `session-env/` under it at runtime, so the directory itself must
  stay writable. Hence the per-file mount strategy.
- Codex requires `ca-certificates` and `git` installed in the container.
- Gemini CLI needs a writable `~/.gemini/` directory (writes `projects.json`
  at startup), so auth files are copied in rather than mounted read-only.

See `scripts/smoke-test-docker-auth.sh` and the per-agent smoke scripts for the
tested mounting commands.

### 6.3 Network Policy

Original intended policy: containers would be created with restricted network
access, allowing only traffic to the agent's API host:

- Claude Code: `api.anthropic.com`
- Codex CLI: `chatgpt.com` (not `api.openai.com` — Codex uses WebSocket)
- Gemini CLI: `generativelanguage.googleapis.com`, `oauth2.googleapis.com`

Under that original offline/API-only condition, all other outbound traffic
would be dropped. The agent would not be able to fetch packages, clone
repositories, or contact any other external service.

**Known historical issue.** A May 2026 audit found that this policy was
documented and represented by adapter `allowed_hosts` declarations, but not
actually enforced for historical agent runs: the runner created agent
containers on Docker's default bridge network. Some published Codex CLI /
OpenAI transcripts contain real `web_search` events as a result. Published
Claude Code / Anthropic transcripts audited at the same time advertised
`WebSearch` / `WebFetch` tools but showed no actual web tool-use events and
zero reported web-search/web-fetch requests.

**Current study policy.** Because published results already used this effective
access level, changing egress or disabling web-search tools mid-study would
create a new experimental condition. Continue using the same effective access
level for the current study, and treat any future API-only/offline runs as a
separate, clearly labeled run series. See `Agent-Run-Notes.md` before
publishing or comparing agent results across network-access conditions.

### 6.4 Resource Limits

| Resource | Limit | Rationale |
|----------|-------|-----------|
| Wall-clock time | 24-hour safety backstop | Avoids killing legitimate long-running agent sessions while still containing hangs |
| Memory | 8 GB | Generous for compilation; prevents runaway allocation |
| CPU | 4 cores | Consistent across runs; enough for parallel cmake |
| Disk | 10 GB | Ample for source + build artifacts |

### 6.5 Container Lifecycle

```
1. docker create  (image, env vars, resource limits, network)
2. docker cp      (prompt + docs → /workspace/prompt/)
3. docker start
4. docker exec    (agent invoke command)
5. wait           (poll for exit or timeout)
6. docker cp      (agent's /workspace/output/ → host)
7. docker rm -f   (cleanup)
```

The harness never enters the container interactively. All interaction is
through `docker exec` and `docker cp`.

---

## 7. Runner: Single-Run Pipeline

The runner orchestrates one complete evaluation run. It is the central
coordination point that calls into Docker, the agent adapter, the build
system, the test runner, and the scoring modules.

### 7.1 Pipeline Steps

```
prepare_workspace()
  → Assemble prompt file (base + language requirements + technical requirements)
  → Copy documentation corpus

run_agent()
  → Build/pull Docker image
  → Create container with sandbox constraints
  → Copy workspace into container
  → Invoke agent via adapter
  → Monitor for completion, timeout, or token limit
  → Extract agent's working directory from container
  → Collect agent result (exit reason, timing, token usage)

build_submission()
  → Eval pytest conftest prepares the language target through the shared plugin
  → C++ uses CMake, Python/JavaScript use entrypoints, Rust uses Cargo

run_pytest_suite()
  → pytest <test-dir> --json-report --json-report-file=<path>
  → Point tests at the prepared submission via --implementation-root and --language
  → Capture per-test pass/fail/skip/error with durations

assemble_result()
  → Compute correctness and per-test-file capability breakdowns
  → Add token usage, cost estimate/source, source stats, and artifacts
  → Write to transient_results/<task>/<agent>/run-<N>.json
```

### 7.2 Timeout Handling

When the wall-clock timeout is reached:

1. Send SIGTERM to the agent process inside the container.
2. Wait 10 seconds for graceful shutdown.
3. If still running, `docker kill` the container.
4. Extract whatever files exist in the working directory.
5. Proceed with build and scoring on the partial output.
6. Record `exit_reason: "timeout"` in the result.

This matches the design doc's intent: "the harness scores whatever files
exist in the working directory at that point."

---

## 8. Result Schema

Each run produces one JSON file. The schema is designed for both human
inspection and programmatic aggregation.

```json
{
  "schema_version": "2.0",

  "metadata": {
    "run_uid": "e81e6027-5353-479b-babd-cff232765773",
    "task": "rs274-cpp",
    "agent": "claude-code",
    "agent_version": "1.0.16",
    "prompt_variant": "base",
    "run_number": 1,
    "timestamp": "2026-03-31T14:22:00Z",
    "test_suite_version": "abc1234",
    "eval_version": "2.1.1",
    "harness_version": "0.1.0",
    "docker_image_sha": "sha256:...",
    "wall_clock_seconds": 1423.7,
    "exit_reason": "completed",
    "model": "claude-opus-4-6",
    "effort": null,
    "prompt_content_sha": "sha256...",
    "test_suite_sha": "sha256..."
  },

  "token_usage": {
    "input_tokens": 247630,
    "output_tokens": 84210,
    "cache_read_input_tokens": 200000,
    "cache_creation_input_tokens": null,
    "reported_cost_usd": null,
    "estimated_cost_usd": 2.41,
    "source": "otel",
    "is_partial": false
  },

  "build": {
    "success": true,
    "duration_seconds": 12.3,
    "diagnostics": ""
  },

  "tests": [
    {
      "node_id": "test_linear_motion.py::test_g0_rapid_move",
      "outcome": "passed",
      "duration_seconds": 0.12,
      "message": null
    },
    {
      "node_id": "test_arc_errors.py::test_arc_missing_endpoint",
      "outcome": "failed",
      "duration_seconds": 0.08,
      "message": "AssertionError: expected error 'endpoint not on arc' but got success"
    }
  ],

  "test_summary": {
    "passed": 142,
    "failed": 3,
    "skipped": 0,
    "error": 1,
    "total": 146
  },

  "scores": {
    "correctness": 0.87,
    "self_test_coverage": null,
    "code_quality": null,
    "task_score": 0.87,
    "extension_scores": {
      "subscore.parser.passed": 91.0,
      "subscore.parser.total": 100.0
    }
  },

  "source_stats": {
    "file_count": 14,
    "lines_of_code": 1820
  }
}
```

### 8.1 Result Directory Structure

Each run produces a result JSON file plus two preserved artifacts: the full
agent transcript and the complete source code directory.

```
transient_results/
  rs274-cpp/
    claude-code/
      eval1/
        run1/
          result.json            # Structured result (scores, tests, metadata)
          transcript.jsonl       # Full agent stdout/stderr transcript
          transcript.canonical.jsonl  # Agent-native transcript, when available
          source/                # Complete source tree the agent produced
        run2/
          result.json
          transcript.jsonl
          source/
    codex-cli/
      gpt-5.4_xhigh/
        eval1/
          run1/
            result.json
            transcript.jsonl
            source/
```

The result JSON includes an `artifacts` field with relative paths:

```json
{
  "artifacts": {
    "transcript": "transcript.jsonl",
    "source_dir": "source"
  }
}
```

### 8.2 Aggregation Queries

The flat per-run JSON structure supports common analysis patterns directly:

**Which tests did no model pass?**
Load all result files, collect the set of `node_id`s with `outcome: "failed"`
for every run, intersect.

**Per-model pass rate over 3 runs (mean +/- stddev):**
Group by `agent`, compute `test_summary.passed / test_summary.total` per run,
report statistics.

**Token efficiency:**
Compare `token_usage.total_tokens` to `scores.correctness` across agents.

**Flaky tests:**
For a given agent, find `node_id`s where `outcome` varies across runs.

---

## 9. CLI Interface

```
clispecbench run
    --task <task-id-or-eval>           # Required: rs274-cpp, bibtex, ...
    --language <lang>                  # Required only when --task is a bare eval name
    --agent <agent-name>               # Required: claude-code, codex-cli, copilot-cli, gemini-cli, opencode, openhands
    --runs <N>                         # Default: 3
    --prompt-variant <name>            # Default: base
    --skip-extensions                  # Skip extension tasks
    --output-dir <path>                # Default: transient_results/
    --model <model-id>                 # Override the default model for the chosen agent (e.g. claude-opus-4-6)
    --effort <level>                   # Optional model effort/reasoning level
    --api-key-env <VAR=value>          # Repeatable: inject secrets into container

clispecbench results
    --task <task-id>                   # Filter by task
    --agent <agent-name>               # Filter by agent
    --format table|json|csv            # Output format
    --compare                          # Side-by-side comparison across agents
    --breakdown                        # Per-capability subscore table
    --flakiness                        # Repeated-run disagreement analysis

clispecbench publish <result.json>
    --status <label>
    --last-message <summary>
    --rebuild-dashboard

clispecbench validate
    --task <task-id>                   # Validate task structure and harness

clispecbench hash
    --task <task-id>
    --show-manifest                    # Print prompt/test hash inputs
```

### 9.1 Examples

```bash
# Run Claude Code against RS274 C++, 3 runs, base prompt
clispecbench run --task rs274-cpp --agent claude-code

# Run Codex CLI against RS274 C++ with a specific model and effort
clispecbench run --task rs274-cpp --agent codex-cli \
    --model gpt-5.4 --effort xhigh

# Compare results across agents for a task
clispecbench results --task rs274-cpp --compare
```

---

## 10. Extension Task Flow

When a task defines extension tasks and `--skip-extensions` is not passed,
the runner continues after base scoring:

```
for each extension in task.extensions:
    1. Append extension prompt to the running agent session inside the container
    2. Wait for agent to finish modifying code (same timeout rules)
    3. Rebuild submission
    4. Run extension-specific hidden tests
    5. Record extension score in result JSON
```

Extensions are sequential — each builds on the state left by the previous
one. This tests whether the agent can make incremental modifications to its
own code without breaking prior functionality.

---

## 11. Token Usage Collection

Token usage is a first-class result dimension, not an afterthought. It enables
analysis of token efficiency (correctness per token) and cost estimation.

### 11.1 Collection Strategy Per Agent

| Agent | Collection method | Granularity |
|-------|-------------------|-------------|
| Claude Code | Parse stream-JSON `result` usage; fallback to OpenTelemetry file export | Per-metric-type (input, output, cache_read, cache_creation) |
| Codex CLI | Parse `turn.completed.usage` from `codex exec --json`; if absent, parse latest session-rollout `token_count` snapshot from `/root/.codex/sessions/` | Completed-turn total; fallback is last completed model-response snapshot |
| Copilot CLI | Prefer OTel file export; fallback to JSON event stream when available | Session total, often output-only on fallback |
| Gemini CLI | Parse stream-JSON final `result.stats` | Session total |
| OpenCode | Parse OpenCode JSON `step_finish` events and preserved data directory | Step/session aggregate |
| OpenHands | Parse persisted `base_state.json` stats from the OpenHands conversation state | Conversation aggregate |

### 11.2 Normalized Schema

All adapters normalize to:

```python
@dataclass
class TokenUsage:
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int | None = None
    cache_creation_input_tokens: int | None = None
    tool_calls: int | None = None
    reported_cost_usd: float | None = None
    estimated_cost_usd: float | None = None
    cost_estimate_blocked_reason: str | None = None
    source: str | None = None
    is_partial: bool = False
```

`total_tokens` is computed as `input_tokens + output_tokens` in the serialized
result. `source` records the telemetry path that produced the measurement, and
`is_partial` is set when the adapter can only prove usage through an intermediate
completed response.

### 11.3 Limitations

- Token counts are best-effort. If an agent crashes or is force-killed,
  partial usage may be lost. The result records `token_usage: null` in this
  case rather than inventing a number.
- Codex session-rollout fallback is not visible-log estimation. It uses
  Codex's own persisted `token_count` events, but failed provider streams still
  have no exact token report until Codex receives `response.completed`.
- Different agents count tokens differently (tokenizer differences, whether
  system prompts are counted, etc.). Cross-agent token comparisons are
  directionally useful but not exact apples-to-apples.
- Cost estimation is best-effort inside the harness. The result preserves both
  raw CLI-reported cost and harness-estimated cost when available, and records
  which source should be used for benchmark reporting. Pricing still changes
  frequently and varies by account type, so published summaries should make the
  cost source clear.

---

## 12. Reproducibility

Every result file contains enough metadata to reproduce the run:

| Field | Purpose |
|-------|---------|
| `agent_version` | Exact CLI version string |
| `eval_version` | Eval contract/test-suite version from `Evals/<Task>/VERSION` |
| `harness_version` | Installed `clispecbench` package version, when available |
| `test_suite_version` | Git SHA of the repository that produced the run |
| `prompt_content_sha` | Content hash over the assembled prompt and docs |
| `test_suite_sha` | Content hash over the pytest suite |
| `docker_image_sha` | Exact container image used |
| `prompt_variant` | Which prompt was used |
| `model` / `effort` | Model override and reasoning/effort setting |
| `timestamp` | When the run started |

Docker images are tagged with both a human-readable version and a content
hash. The harness records the SHA, not the tag, so that results remain
traceable even if a tag is moved.

---

## 13. Open Design Questions

- **Telemetry source consistency.** Adapters currently use the most reliable
  source each CLI exposes: stream JSON, OTel file export, persisted session
  state, or a combination. That is practical, but cross-agent token comparisons
  should continue to surface the source and `is_partial` flag prominently.

- **Agent session persistence for extensions.** Extension prompts should be
  injected into the *same* session so the agent retains context about its own
  code. Whether all agent CLIs support appending to a running session (vs.
  starting a new one with the prior source files as context) needs
  investigation per agent.

- **Parallel runs.** Running repetitions sequentially is slow. Parallel runs
  are feasible if Docker resources allow, but concurrent API calls to the same
  model endpoint may introduce rate-limit variance. The runner should support
  `--parallel` eventually, while keeping explicit local queue scripts for
  operational sweeps until that path is mature.

- **Self-test detection.** The harness needs to identify which files are the
  agent's self-written tests (for coverage scoring). Heuristics: files in a
  `tests/` or `test/` directory, files matching `test_*.py` or `*_test.cpp`.
  This may need to be configurable per task if agents use non-standard layouts.
