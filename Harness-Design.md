# SWE-BuildBench Evaluation Harness — Design Document

**Author:** Matthew G. Knutson
**Status:** Draft
**Last Updated:** April 2026

---

> **Note on CNCSim naming.** The current harness exposes explicit language task
> IDs such as `cncsim-cpp`, `cncsim-py`, `cncsim-js`, and `cncsim-rs`. The
> current repository ships a single `Evals/CNCSim/` eval. See
> `Evals/CNCSim/README.md`.

## 1. Purpose

This document describes the evaluation harness: the software that invokes AI
coding agents (or model APIs) against SWE-BuildBench tasks, captures their
output, builds it, runs the hidden test suite, and records structured results.

It is a companion to `Eval-Design.md`, which defines the benchmark's
scoring model, task anatomy, and evaluation modes. This document covers the
harness implementation: how those concepts become running code.

---

## 2. Goals

1. **Run any supported agent against any task with a single command.**
   `swe-buildbench run --task cncsim-cpp --agent claude-code`

2. **Produce structured, machine-readable results** that capture per-test
   pass/fail, token usage, timing, and scoring — enabling cross-model and
   cross-task analysis.

3. **Sandbox agent execution** so that agents cannot affect the host, contact
   external services (beyond their own API), or observe the hidden test suite.

4. **Be agent-agnostic.** Adding a new agent CLI should require only a small
   adapter module, not changes to the core harness.

5. **Support both evaluation modes** (agentic CLI and model API) through the
   same scoring pipeline.

---

## 3. Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│  swe-buildbench CLI                                  │
│                                                      │
│  run --task <id> --agent <name> [--runs N] ...       │
└──────────┬───────────────────────────────────────────┘
           │
           ▼
┌──────────────────────┐     ┌──────────────────────┐
│  Task Registry       │     │  Agent Registry       │
│                      │     │                       │
│  Loads TASK.md,      │     │  Selects adapter for  │
│  prompts, test suite │     │  the named agent      │
└──────────┬───────────┘     └──────────┬────────────┘
           │                            │
           ▼                            ▼
┌──────────────────────────────────────────────────────┐
│  Runner (orchestrates one eval run)                  │
│                                                      │
│  1. Prepare workspace (prompt + docs)                │
│  2. Build & start Docker container                   │
│  3. Invoke agent via adapter                         │
│  4. Wait for completion or timeout                   │
│  5. Extract workspace from container                 │
│  6. Build submission (cmake)                         │
│  7. Run hidden test suite (pytest --json-report)     │
│  8. Run self-test coverage (gcov/lcov)               │
│  9. Run code quality eval (LLM judge)                │
│  10. Collect token usage from adapter                │
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
src/swe_buildbench/
  __init__.py
  cli.py                        # CLI entry point (swe-buildbench command)

  harness/
    __init__.py
    runner.py                   # Orchestrates a single eval run end-to-end
    docker.py                   # Container lifecycle management
    task.py                     # Task registry: loads prompts, tests
    workspace.py                # Prepares the clean working directory for the agent
    scoring.py                  # Correctness, coverage, quality scoring
    results.py                  # Result schema, serialization, aggregation

  agents/
    __init__.py
    base.py                     # Abstract AgentAdapter interface
    claude_code.py              # Claude Code CLI adapter
    codex_cli.py                # Codex CLI adapter
    gemini_cli.py               # Gemini CLI adapter
    model_api.py                # Model API mode adapter (direct API calls)

  build/                        # Shared CMake build utilities
    build.py                    # build_cmake_project, CMakeBuildResult
    target.py                   # ImplementationTarget, find_repo_root

  cncsim/                       # CNCSim-specific test infrastructure
    target.py                   # CNCSim default implementation target resolution
    rs274_parameters.py         # RS274 parameter constants
    modal_groups.py             # Modal group constants
    test_support.py             # Test helpers (run_cncsim, parameter files, etc.)

Evals/
  _shared/                          # Shared across evals
    language-requirements-cpp.md        # C++ boilerplate
    language-requirements-py.md         # Python boilerplate
    language-requirements-js.md         # JavaScript boilerplate
    language-requirements-rs.md         # Rust boilerplate
  CNCSim/                           # CNC G-code interpreter eval
    prompt/ docs/ tests/
    reference-implementation-cpp/       # C++ reference
    reference-implementation-py/        # Python reference
    reference-implementation-js/        # JavaScript reference
  WordCount/                        # Word frequency counter (toy eval)
    prompt/ docs/ tests/
    reference-implementation-cpp/
    reference-implementation-py/
    reference-implementation-js/

docker/
  base.Dockerfile               # Common: C++20 toolchain, cmake, python, pytest
  agents/
    claude-code.Dockerfile      # Extends base, installs Claude Code CLI
    codex-cli.Dockerfile        # Extends base, installs Codex CLI
    gemini-cli.Dockerfile       # Extends base, installs Gemini CLI

scripts/
  install-docker-wsl.sh         # Docker Engine install in WSL2 Ubuntu
  smoke-test-docker-auth.sh     # Verify CLI auth works inside containers
```

---

## 5. Agent Adapter Interface

Each supported agent implements this interface. The harness interacts with
agents only through this abstraction.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TokenUsage:
    """Normalized token usage from any agent."""
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int | None = None
    total_tokens: int | None = None


@dataclass
class AgentResult:
    """What the adapter returns after an agent run completes."""
    exit_reason: str              # "completed" | "timeout" | "token_limit" | "error"
    wall_clock_seconds: float
    token_usage: TokenUsage | None
    raw_log_path: Path | None     # Agent-specific log (for debugging, not scoring)


class AgentAdapter(ABC):
    """Abstract base for all agent adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent identifier used in results and CLI (e.g., "claude-code")."""

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
        prompt_path: Path,
        work_dir: Path,
    ) -> list[str]:
        """The shell command to start the agent inside the container.

        prompt_path: path (inside the container) to the assembled prompt file.
        work_dir: path (inside the container) to the clean working directory.
        Returns: command + args as a list of strings.
        """

    @abstractmethod
    def parse_token_usage(self, container_fs: Path) -> TokenUsage | None:
        """Extract token usage from agent-specific logs or telemetry.

        container_fs: root of the extracted container filesystem.
        Returns: normalized TokenUsage, or None if unavailable.
        """
```

### 5.1 Adapter Implementation Notes

**Claude Code.** Invoked via `claude --print` with `--output-format stream-json`.
Token usage is extracted from OpenTelemetry metrics exported to a local file
collector configured inside the container. The adapter sets
`OTEL_METRICS_EXPORTER=otlp` and `OTEL_EXPORTER_OTLP_ENDPOINT` to a file-based
collector endpoint, then parses the `claude_code.token.usage` metric from the
exported data after the run completes.

**Codex CLI.** Invoked via `codex exec --json`. Token usage is parsed directly
from the JSONL event stream — `turn.completed` events contain `input_tokens`,
`cached_input_tokens`, and `output_tokens`. The adapter sums across all turns.

**Gemini CLI.** Invoked in non-interactive mode. Token usage is extracted via
OpenTelemetry export (similar to Claude Code) or parsed from the `/stats`
output captured at session end.

**Model API.** No Docker container. The adapter calls the model API directly
from the host, parses the structured JSON file envelope from the response,
writes files to disk, and returns token counts from the API response's `usage`
field. The rest of the pipeline (build, test, score) proceeds identically.

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
    && rm -rf /var/lib/apt/lists/*

# Pin compiler version for reproducibility
ENV CC=gcc-14 CXX=g++-14

WORKDIR /workspace
```

```dockerfile
# docker/agents/claude-code.Dockerfile
FROM swe-buildbench-base:latest

RUN npm install -g @anthropic-ai/claude-code@<pinned-version>

# OpenTelemetry file collector for token tracking
COPY otel-collector-config.yaml /etc/otel/
```

### 6.2 Authentication

Agent CLIs authenticate via OAuth tokens stored on the host machine. The
harness mounts host credential files into the container at runtime. Each
agent has different requirements (verified via smoke testing):

| Agent | Host files | Mount strategy |
|-------|-----------|----------------|
| Claude Code | `~/.claude/` (read-only), `~/.claude.json` (read-only) | Direct `:ro` bind mounts |
| Codex CLI | `~/.codex/auth.json` (read-only, file only) | Mount single file `:ro`; rest of `.codex/` stays writable |
| Gemini CLI | `~/.gemini/oauth_creds.json`, `google_accounts.json`, `settings.json` | Copy to writable dir at startup; seed `projects.json` |

Notes:
- Claude Code needs `~/.claude.json` (config file) mounted or its warning
  messages corrupt stdout.
- Codex requires `ca-certificates` and `git` installed in the container.
- Gemini CLI needs a writable `~/.gemini/` directory (writes `projects.json`
  at startup), so auth files are copied in rather than mounted read-only.

See `scripts/smoke-test-docker-auth.sh` for the tested mounting commands.

### 6.3 Network Policy

Containers are created with restricted network access, allowing only traffic
to the agent's API host:

- Claude Code: `api.anthropic.com`
- Codex CLI: `chatgpt.com` (not `api.openai.com` — Codex uses WebSocket)
- Gemini CLI: `generativelanguage.googleapis.com`, `oauth2.googleapis.com`

All other outbound traffic is dropped. The agent cannot fetch packages, clone
repositories, or contact any other external service.

### 6.4 Resource Limits

| Resource | Limit | Rationale |
|----------|-------|-----------|
| Wall-clock time | 30 minutes | Per Eval-Design.md Section 5.3 |
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
  → Assemble prompt file (base + technical requirements)
  → Copy documentation corpus
  → Write any task-specific config files (tool table, parameter file)

run_agent()
  → Build/pull Docker image
  → Create container with sandbox constraints
  → Copy workspace into container
  → Invoke agent via adapter
  → Monitor for completion, timeout, or token limit
  → Extract agent's working directory from container
  → Collect agent result (exit reason, timing, token usage)

build_submission()
  → Run the task's build.sh (or cmake directly for C++ tasks)
  → Record build success/failure and any compiler diagnostics

run_hidden_tests()
  → pytest <test-dir> --json-report --json-report-file=<path>
  → Point tests at the built executable via --executable flag
  → Capture per-test pass/fail/skip/error with durations

run_self_test_coverage()     (if agent wrote tests)
  → Rebuild with --coverage flags
  → Run agent's own tests
  → Parse gcov/lcov output for line coverage percentage

run_quality_eval()
  → Send each source file + rubric guideline to LLM judge
  → Collect per-guideline pass/fail/not-applicable

assemble_result()
  → Combine all scores and metadata into result JSON
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
  "schema_version": "1.0",

  "metadata": {
    "run_id": "cncsim-cpp_claude-code_2026-03-31_run-1",
    "task": "cncsim-cpp",
    "agent": "claude-code",
    "agent_version": "1.0.16",
    "prompt_variant": "base",
    "run_number": 1,
    "timestamp": "2026-03-31T14:22:00Z",
    "test_suite_version": "abc1234",
    "docker_image_sha": "sha256:...",
    "wall_clock_seconds": 1423.7,
    "exit_reason": "completed"
  },

  "token_usage": {
    "input_tokens": 247630,
    "output_tokens": 84210,
    "cached_input_tokens": 200000,
    "total_tokens": 331840
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
    "self_test_coverage": 0.72,
    "code_quality": 0.81,
    "task_score": 0.826,
    "extension_scores": {}
  }
}
```

### 8.1 Result Directory Structure

Each run produces a result JSON file plus two preserved artifacts: the full
agent transcript and the complete source code directory.

```
transient_results/
  cncsim-cpp/
    claude-code/
      run-1.json                 # Structured result (scores, tests, metadata)
      run-1-transcript.jsonl     # Full agent conversation/event log
      run-1-source/              # Complete source tree the agent produced
      run-2.json
      run-2-transcript.jsonl
      run-2-source/
      ...
    codex-cli/
      run-1.json
      run-1-transcript.jsonl
      run-1-source/
      ...
```

The result JSON includes an `artifacts` field with relative paths:

```json
{
  "artifacts": {
    "transcript": "run-1-transcript.jsonl",
    "source_dir": "run-1-source"
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
swe-buildbench run
    --task <task-id>                   # Required: cncsim-cpp, cncsim-py, wordcount-cpp, ...
    --agent <agent-name>               # Required: claude-code, codex-cli, gemini-cli, model-api
    --runs <N>                         # Default: 3 for agentic, 1 for model-api
    --prompt-variant <name>            # Default: base
    --skip-extensions                  # Skip extension tasks
    --output-dir <path>                # Default: transient_results/
    --model <model-id>                 # For model-api mode: claude-opus-4-6, gpt-4o, etc.
    --api-key-env <VAR=value>          # Repeatable: inject secrets into container

swe-buildbench results
    --task <task-id>                   # Filter by task
    --agent <agent-name>               # Filter by agent
    --format table|json|csv            # Output format
    --compare                          # Side-by-side comparison across agents

swe-buildbench validate
    --task <task-id>                   # Validate task structure and harness
```

### 9.1 Examples

```bash
# Run Claude Code against CNCSim C++, 3 runs, base prompt
swe-buildbench run --task cncsim-cpp --agent claude-code \
    --api-key-env ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# Run Codex CLI against CNCSim C++ with the "with-tests" prompt variant
swe-buildbench run --task cncsim-cpp --agent codex-cli \
    --prompt-variant with-tests \
    --api-key-env OPENAI_API_KEY=$OPENAI_API_KEY

# Run a model API evaluation (single run, no Docker)
swe-buildbench run --task cncsim-cpp --agent model-api \
    --model claude-opus-4-6 --runs 1 \
    --api-key-env ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# Compare results across agents for a task
swe-buildbench results --task cncsim-cpp --compare
```

---

## 10. Extension Task Flow

When a task defines extension tasks and `--skip-extensions` is not passed,
the runner continues after base scoring:

```
for each extension in task.extensions:
    1. Inject extension prompt into the active agent session
       - Agentic: append to the running session inside the container
       - Model API: new API call with agent's source files as context
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
| Claude Code | OpenTelemetry file export inside container; parse `claude_code.token.usage` metric | Per-metric-type (input, output, cache_read, cache_creation) |
| Codex CLI | Parse JSONL event stream from `codex exec --json`; sum `turn.completed` events | Per-turn, summed to session total |
| Gemini CLI | OpenTelemetry export or capture `/stats` output at session end | Session total |
| Model API | Read `usage` field from API response object | Per-request (typically one request) |

### 11.2 Normalized Schema

All adapters normalize to:

```python
@dataclass
class TokenUsage:
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int | None = None
    total_tokens: int | None = None
```

`total_tokens` is computed as `input_tokens + output_tokens` if not provided
natively. `cached_input_tokens` is null for agents that don't report it.

### 11.3 Limitations

- Token counts are best-effort. If an agent crashes or is force-killed,
  partial usage may be lost. The result records `token_usage: null` in this
  case rather than inventing a number.
- Different agents count tokens differently (tokenizer differences, whether
  system prompts are counted, etc.). Cross-agent token comparisons are
  directionally useful but not exact apples-to-apples.
- Cost estimation is left to downstream analysis, not the harness. Token
  pricing changes frequently and varies by account type.

---

## 12. Reproducibility

Every result file contains enough metadata to reproduce the run:

| Field | Purpose |
|-------|---------|
| `agent_version` | Exact CLI version string |
| `test_suite_version` | Git SHA of the private test repo |
| `docker_image_sha` | Exact container image used |
| `prompt_variant` | Which prompt was used |
| `timestamp` | When the run started |

Docker images are tagged with both a human-readable version and a content
hash. The harness records the SHA, not the tag, so that results remain
traceable even if a tag is moved.

---

## 13. Open Design Questions

- **OpenTelemetry collector in container.** Running an OTLP collector inside
  each agent container adds complexity. An alternative is to mount a host
  directory and configure the agent to write telemetry files directly. This
  is simpler but couples the agent's telemetry config to the harness.

- **Agent session persistence for extensions.** In agentic mode, extension
  prompts should be injected into the *same* session so the agent retains
  context about its own code. Whether all agent CLIs support appending to a
  running session (vs. starting a new one with files as context) needs
  investigation per agent.

- **Parallel runs.** Running 3 repetitions sequentially is slow (up to 90
  minutes per agent per task). Parallel runs are feasible if Docker resources
  allow, but concurrent API calls to the same model endpoint may introduce
  rate-limit variance. The runner should support `--parallel` but default to
  sequential.

- **Self-test detection.** The harness needs to identify which files are the
  agent's self-written tests (for coverage scoring). Heuristics: files in a
  `tests/` or `test/` directory, files matching `test_*.py` or `*_test.cpp`.
  This may need to be configurable per task if agents use non-standard layouts.

- **Model API structured output reliability.** Some models may not reliably
  produce valid JSON matching the file envelope schema. The harness should
  attempt to parse, and if parsing fails, record `build.success: false` with
  the parse error — not silently skip the run.
