# SWE-BuildBench

A benchmark suite for evaluating AI coding agents on documentation-driven
implementation tasks. Agents receive a specification and domain docs, then must
produce a working C++ implementation that passes a hidden test suite.

## Repository Layout

```
Evals/                   # Evaluation tasks (one directory per task)
  CNCSim/                #   CNC G-code interpreter (full benchmark task)
  WordCount/             #   Word frequency counter (toy eval for harness testing)
src/swe_buildbench/      # Python package: harness, agent adapters, shared build utils
docker/                  # Dockerfiles (base image + per-agent images)
scripts/                 # Setup and utility scripts
```

Design docs:

- `SWE-BuildBench-Design.md` -- benchmark-level design (scoring, task anatomy, eval modes)
- `Harness-Design.md` -- evaluation harness architecture and implementation
- `Evals/CNCSim/README.md` -- CNCSim task design and test categories

## Requirements

- **Python 3.11+** with [uv](https://docs.astral.sh/uv/) (or pip)
- **CMake** and a C++20 compiler (gcc-14, clang, or MSVC)
- **Docker Engine** in WSL2 (Windows) or native Docker (Linux/macOS)
- **Node.js 22+** (installed in Docker images for CLI agents)

## Environment Setup

### 1. Install Python dependencies

```bash
uv sync          # or: pip install -e ".[dev]"
```

### 2. Install Docker (Windows)

Run the install script from a WSL terminal (requires sudo password):

```bash
wsl -d Ubuntu
bash /mnt/c/Git/SWE-BuildBench/scripts/install-docker-wsl.sh
```

After install, add your user to the docker group and restart WSL:

```bash
sudo usermod -aG docker $USER
exit
wsl --shutdown
```

### 3. Authenticate CLI agents

Log in to each agent CLI on your host machine:

```bash
claude login          # Claude Code
codex login           # Codex CLI
gemini auth login     # Gemini CLI
```

The harness mounts host credential files into Docker containers at runtime.
See `scripts/smoke-test-docker-auth.sh` for the per-agent mounting strategy and
to verify authentication works inside containers.

## How Evals Work

Each eval task follows a standard pipeline:

1. **Prompt assembly** -- The harness concatenates the base prompt (domain expert
   persona) with the technical requirements prompt, and includes the docs directory.

2. **Agent invocation** -- The agent CLI runs inside a Docker container with the
   prompt and docs mounted. Network access is restricted to the agent's API host.
   Host auth credentials are mounted read-only.

3. **Build** -- The agent's output is built with CMake inside the sandbox.

4. **Test** -- The hidden pytest test suite runs against the built executable.
   Results are captured as structured JSON via pytest-json-report.

5. **Scoring** -- Per-test pass/fail, token usage, timing, and composite scores
   are written to a `RunResult` JSON file.

## Running an Eval

```bash
swe-buildbench run --task wordcount --agent claude-code
swe-buildbench run --task cncsim-full --agent codex-cli
```

View results:

```bash
swe-buildbench results
```

## Running Tests Locally

Run a task's test suite against its reference implementation:

```bash
# CNCSim
pytest Evals/CNCSim/tests

# WordCount
pytest Evals/WordCount/tests
```

Point tests at a different implementation:

```bash
pytest Evals/WordCount/tests --implementation-root /path/to/agent-output
```

## Adding a New Eval

Each eval lives in its own directory under `Evals/`. Required structure:

```
Evals/MyTask/
  prompt/
    base-prompt.md                    # Non-technical domain expert persona
    technical-requirements-prompt.md  # Harness contract (language, CLI, output format)
    docs/                             # Domain documentation provided to the agent
  tests/
    conftest.py                       # Build fixtures and test helpers
    test_build.py                     # Verifies cmake build succeeds
    test_*.py                         # Hidden test suite
  reference-implementation/
    CMakeLists.txt                    # CMake project
    src/                              # Reference solution (must pass all tests)
```

Then register the task in `src/swe_buildbench/harness/task.py`:

```python
_KNOWN_TASKS: dict[str, str] = {
    ...
    "mytask": "Evals/MyTask",
}
```

The reference implementation should pass all tests before committing. Verify:

```bash
pytest Evals/MyTask/tests -v
```

### Prompt authoring guidelines

- `base-prompt.md` should describe the task from a domain expert perspective
  without engineering guidance. The agent should figure out the implementation.
- `technical-requirements-prompt.md` defines only what the harness needs to
  build and test: language/tooling constraints, CLI flags, exit codes, output
  schema. Do not put domain behavior here.
- `docs/` contains reference material the agent can use (specs, standards, etc.).

## Line Endings

This repository enforces LF line endings via `.gitattributes`.

On Windows, keep Git configured for LF-friendly behavior:

```powershell
git config --global core.autocrlf false
git config --global core.safecrlf true
```
