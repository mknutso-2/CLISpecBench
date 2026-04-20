# CLISpecBench

A benchmark suite for evaluating AI coding agents on documentation-driven
implementation tasks. Agents receive a specification and domain docs, then must
produce a working implementation that passes a hidden test suite. Tasks may
expose one or more target languages; the harness currently supports C++,
Python, JavaScript, and Rust, with a shared test suite verifying each
submission through a language-agnostic CLI contract.

## Core Concepts

The repo is easier to navigate if you separate five concepts:

| Concept | Meaning | Main locations |
|---|---|---|
| **Coding agent** | The external tool being benchmarked. Today this is usually one of `claude-code`, `codex-cli`, `copilot-cli`, or `gemini-cli`. | Wrapped by files under `src/clispecbench/agents/` and containerized from `docker/agents/` |
| **Eval** | A benchmark task: prompt materials, hidden tests, and reference implementations for one problem domain. | `Evals/<Task>/` |
| **Task** | A harness-visible eval-language pair. This is what `clispecbench run --task ...` and `clispecbench validate --task ...` operate on. Examples: `wordcount-cpp`, `wordcount-rs`, `rs274-js`. | Registered in `src/clispecbench/harness/task.py` |
| **Eval harness** | The repo code that prepares prompts, runs agents, builds submissions, runs hidden tests, scores results, and records metadata. | `src/clispecbench/harness/`, `src/clispecbench/build/`, `src/clispecbench/cli.py` |
| **Repo tests** | Tests for the harness, build backends, and agent adapters themselves. These are distinct from an eval's hidden tests. | `src/clispecbench/tests/` |

Two useful distinctions:

- A **coding agent** is the external product being benchmarked.
- An **agent adapter** is this repo's wrapper for that coding agent: auth mounting,
  Docker image selection, CLI invocation, and token/message extraction.

## Repository Layout

```
Evals/                   # Evaluation tasks (one directory per task)
  _shared/               #   Shared language-requirements prompts
  RS274/                #   CNC G-code interpreter (full benchmark task)
  IGES/                  #   IGES CAD interchange parser/writer eval
  IGES-SDK/              #   Upstream IGES porting source tree
  WordCount/             #   Word frequency counter (toy eval for harness testing)
src/clispecbench/      # Python package
  agents/                #   One adapter module per coding agent
  build/                 #   Multi-language submission build backends
  harness/               #   Eval orchestration, Docker, scoring, results
  tests/                 #   Harness/adapter/build tests
docker/                  # Dockerfiles (base image + per-agent images)
  agents/                #   One Dockerfile per CLI coding agent
scripts/                 # Setup and utility scripts
```

Design docs:

- `Eval-Design.md` -- benchmark-level design (scoring, task anatomy, eval modes)
- `Harness-Design.md` -- evaluation harness architecture and implementation
- `Evals/RS274/README.md` -- RS274 task design and test categories
- `Evals/IGES/README.md` -- IGES eval design, scope, and contract notes

## Requirements

Requirements depend on what you plan to do on the **host machine**:

- **Always needed on the host**
  - **Python 3.11+** with [uv](https://docs.astral.sh/uv/) (or pip) — needed to
    install dependencies, run `clispecbench`, and run the pure-Python test suite.
  - **Docker Engine** in WSL2 (Windows) or native Docker (Linux/macOS) — needed for
    normal `clispecbench run` usage, container smoke tests, auth smoke tests, and
    any workflow that uses the sandbox images.
- **Needed on the host only for local reference-implementation workflows**
  - **CMake + a C++ compiler** — needed if you run C++ reference implementations or
    point tests at a local C++ submission with `--implementation-root`.
    - **C++20** is the shared prompt/harness baseline and is sufficient for the current
      `RS274` and `WordCount` C++ reference implementations.
    - **C++23-capable compiler** is needed if you also want to build/run the current
      `IGES` C++ reference implementation.
  - **Node.js 22+** — needed only if you run JavaScript reference implementations on
    the host, such as `pytest Evals/WordCount/tests --language=js` or
    `pytest Evals/RS274/tests --language=js`.
  - **Rust stable** via [rustup](https://rustup.rs/) — needed only if you run Rust
    reference implementations on the host, such as
    `pytest Evals/WordCount/tests --language=rs` or `pytest Evals/RS274/tests --language=rs`.
    The repo's shared Rust prompt currently targets **Rust 2021 or later**.
- **Bundled in the Docker images, so not required on the host just to run evals**
  - **Node.js 22+** for the CLI-agent containers
  - **Rust stable** in `docker/base.Dockerfile` for sandbox/test-runner `--language=rs` workflows

## Environment Setup

### 1. Install Python dependencies

```bash
uv sync          # or: pip install -e ".[dev]"
```

### 2. Install Docker (Windows, one-time)

Run the install script from a WSL terminal (requires sudo password).
This only needs to be done once per machine -- Docker persists across reboots.

```bash
wsl -d Ubuntu
bash /mnt/c/Git/CLISpecBench/scripts/install-docker-wsl.sh
```

After install, add your user to the docker group and restart WSL:

```bash
sudo usermod -aG docker $USER
exit
wsl --shutdown
```

### 3. Build Docker images

Build the base image and per-agent images:

```bash
MSYS_NO_PATHCONV=1 bash scripts/build-docker-images.sh
```

This creates `clispecbench-base:latest` (Ubuntu 24.04, CMake, g++-14, pytest)
and CLI agent images (`clispecbench-claude-code`,
`clispecbench-codex-cli`, `clispecbench-copilot-cli`,
`clispecbench-gemini-cli`) that extend it.

### 4. Authenticate CLI agents

Log in to each agent CLI **on the host that runs the Python harness** --
the harness mounts that host's home-directory credentials into the
container at runtime.

- **Windows + WSL2 Docker** (the typical Windows setup): run the CLIs on
  Windows so credentials land in `C:\Users\<you>\.claude\`, `\.codex\`,
  `\.gemini\`, and `C:\Users\<you>\AppData\Roaming\GitHub CLI\hosts.yml`.
  The harness translates these to `/mnt/c/Users/<you>/...` for the WSL2
  daemon. Authenticating inside WSL Ubuntu does **not** work for this setup
  -- the harness never reads the WSL home.
- **Native Linux / macOS**: run the CLIs on the same host where you'll
  invoke `clispecbench`. Credentials in `~/.claude/`, `~/.codex/`,
  `~/.gemini/`, and `~/.config/gh/hosts.yml` are mounted directly.

```bash
claude login          # Claude Code
codex login           # Codex CLI
gh auth login         # GitHub CLI token used by GitHub Copilot CLI
gemini auth login     # Gemini CLI
```

GitHub Copilot CLI can also consume `COPILOT_GITHUB_TOKEN`, `GH_TOKEN`, or
`GITHUB_TOKEN`, but `gh auth login` is the default host-auth path used by the
harness and smoke tests.

To verify auth works end-to-end inside containers, see the **Auth smoke
tests** sub-section under [Running Tests](#running-tests).

## How the Harness Runs an Eval

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
clispecbench run --task wordcount-cpp --agent claude-code
clispecbench run --task rs274-cpp --agent codex-cli
clispecbench run --task iges-cpp --agent copilot-cli
```

View results:

```bash
clispecbench results
```

## Running Tests

This project has four categories of tests. CI runs the first three on
every PR; the fourth is a hand-run diagnostic for new-machine setup.

| Category                                                  | Location                                       | Runner   | Cost                | Prereqs                              |
|-----------------------------------------------------------|------------------------------------------------|----------|---------------------|--------------------------------------|
| [**Eval reference tests**](#eval-reference-tests)         | `Evals/<task>/tests/`                          | `pytest` | No API cost         | C++ toolchain                        |
| [**Harness unit tests**](#harness-tests)                  | `src/clispecbench/tests/` (unmarked)         | `pytest` | No API cost         | `uv sync`                            |
| [**Container smoke tests**](#harness-tests)               | `src/clispecbench/tests/` (`docker` marker)  | `pytest` | No API cost         | Docker daemon + built images         |
| [**Auth smoke tests**](#auth-smoke-tests)                 | `scripts/smoke-test-*.sh`                      | bash     | ~pennies of tokens  | Docker + agent creds + built images  |

### Eval reference tests

Each task's hidden test suite, run against its reference implementation:

```bash
pytest Evals/RS274/tests --language=cpp
pytest Evals/IGES/tests --language=cpp
pytest Evals/WordCount/tests --language=cpp
```

Select a target language explicitly (when multiple reference implementations exist):

```bash
pytest Evals/WordCount/tests --language=py
pytest Evals/WordCount/tests --language=js
pytest Evals/WordCount/tests --language=rs
pytest Evals/WordCount/tests --language=cpp
```

Point tests at a different implementation (e.g. an agent's output):

```bash
pytest Evals/WordCount/tests --language=cpp --implementation-root /path/to/agent-output
pytest Evals/WordCount/tests --language=py --implementation-root /path/to/py-output
```

### Harness tests

The harness has its own pytest suite under `src/clispecbench/tests/`.
Tests are tagged with markers so you can pick a subset:

| Marker          | Meaning                                                      |
|-----------------|--------------------------------------------------------------|
| (unmarked)      | Pure-Python unit tests -- no Docker, no API calls            |
| `docker`        | Spins up real containers; needs Docker daemon + built images |
| `prompts_agent` | Sends a real prompt to an AI coding agent (consumes tokens)  |

Typical filters (mirror what CI runs):

```bash
# Fast unit tests only -- CI's `unit-tests` job
uv run pytest src/clispecbench/tests -m "not docker and not prompts_agent"

# Container smoke tests -- CI's `container-tests` job
# (requires built images -- see "Build Docker images" in Environment Setup)
uv run pytest src/clispecbench/tests -m "docker and not prompts_agent"

# Everything that doesn't cost API tokens
uv run pytest src/clispecbench/tests -m "not prompts_agent"
```

The container tests require the base image and all four CLI agent images to
be built first. From a clean checkout:

```bash
MSYS_NO_PATHCONV=1 bash scripts/build-docker-images.sh
```

(See [3. Build Docker images](#3-build-docker-images) for details.)

#### Windows: pointing pytest at the WSL2 Docker daemon

On Windows, the Python `docker` library's auto-detection doesn't always
find the WSL2 daemon. If a `docker`-marked test fails with
`Cannot connect to Docker daemon`, set `DOCKER_HOST` explicitly:

```bash
DOCKER_HOST=tcp://localhost:2375 uv run pytest src/clispecbench/tests -m "docker and not prompts_agent"
```

This points the harness at the TCP listener that
`scripts/install-docker-wsl.sh` configures on the WSL daemon.

### Auth smoke tests

To verify each agent CLI authenticates correctly inside its container,
run the per-agent smoke-test scripts. These send a one-word prompt
(`"respond with just the word hello"`) to each agent via its real API,
so they consume a small amount of tokens per run.

These tests require the agent images to be built and the CLIs to be
authenticated on the host. From a clean checkout you'll need to run
both setup steps first if you haven't already:

```bash
# 1. Build base + agent images (see "3. Build Docker images" above)
MSYS_NO_PATHCONV=1 bash scripts/build-docker-images.sh

# 2. Log in to each CLI on the host (see "4. Authenticate CLI agents" above)
claude login
codex login
gh auth login
gemini auth login
```

Then run the smoke tests:

```bash
# All four agents in one go
MSYS_NO_PATHCONV=1 bash scripts/smoke-test-docker-auth.sh

# Or individually, for debugging
MSYS_NO_PATHCONV=1 bash scripts/smoke-test-claude.sh
MSYS_NO_PATHCONV=1 bash scripts/smoke-test-codex.sh
MSYS_NO_PATHCONV=1 bash scripts/smoke-test-copilot.sh
MSYS_NO_PATHCONV=1 bash scripts/smoke-test-gemini.sh
```

These are standalone diagnostics -- not part of `pytest` and not run by
CI. They are the right place to look for the per-agent credential
mounting strategy that the harness uses.

## Adding a Coding Agent

Adding a new coding agent is currently spread across a few touchpoints. The
functionality is not fully centralized in one folder yet, so use this checklist.

**Required touchpoints**

1. **Add an adapter module** under `src/clispecbench/agents/` that subclasses
   `AgentAdapter`. This is where invocation, credential mounts, token parsing,
   telemetry paths, and allowed hosts live.
2. **Add a Dockerfile** under `docker/agents/<agent-name>.Dockerfile` for the
   container image that runs that agent.
3. **Add a registry entry** in `src/clispecbench/agents/registry.py`. The
   CLI's adapter resolution and `--agent` choices derive from that registry.
4. **Add adapter tests** in `src/clispecbench/tests/test_agents.py`.
5. **Add container smoke coverage** in `src/clispecbench/tests/test_container_smoke.py`.
6. **Add auth smoke coverage**:
   - create `scripts/smoke-test-<agent>.sh`
   - register that script in `src/clispecbench/agents/registry.py`
7. **Update docs** if the setup or workflow differs from existing agents.

**Helpful notes**

- `scripts/build-docker-images.sh` auto-discovers Dockerfiles under `docker/agents/`,
  so adding the Dockerfile is enough for that script to build the new image.
- For CLI agents, credentials should be exposed through the adapter via
  `credential_mounts()` and/or environment variables.
- If the agent needs special network access, update the adapter's `allowed_hosts`.

## Adding a New Eval

Adding a new eval is already more localized than adding a coding agent. Most of
the work lives under `Evals/<Task>/`; the main repo-wide touchpoint is the task
registry in `src/clispecbench/harness/task.py`.

**Required touchpoints**

1. **Create the eval directory** under `Evals/<Task>/`.
2. **Add the prompt/docs/tests/reference implementation** under that directory.
3. **If the eval should be invokable through the harness CLI**, register one or
   more task IDs in `src/clispecbench/harness/task.py`.
4. **Validate the reference implementation** by running the hidden test suite
   against it before committing.

Each eval lives in its own directory under `Evals/`. Required structure:

```
Evals/MyTask/
  VERSION                                  # Semver string (e.g. 1.0.1)
  CHANGELOG.md                             # Human-readable change history
  prompt/
    base-prompt.md                         # Non-technical domain expert persona
    technical-requirements-prompt.md       # Language-agnostic harness contract
                                           #   (flags, JSON schema, exit codes)
    docs/                                  # Domain documentation provided to the agent
  tests/
    conftest.py                            # Imports shared fixtures + defines EVAL_CONFIG
    test_build.py                          # Verifies the submission is buildable/runnable
    test_*.py                              # Hidden test suite (language-agnostic)
  reference-implementation-cpp/            # C++ reference (optional per-eval)
    CMakeLists.txt
    src/
  reference-implementation-py/             # Python reference (optional per-eval)
    main.py
  reference-implementation-js/             # JavaScript reference (optional per-eval)
    package.json
    src/
  reference-implementation-rs/             # Rust reference (optional per-eval)
    Cargo.toml
    src/main.rs
```

Language-specific boilerplate (target version, stdlib constraint, build
command, entry-point layout) lives in a shared prompt file outside the eval
directory:

```
Evals/_shared/
  language-requirements-cpp.md             # Shared across all C++ evals
  language-requirements-py.md              # Shared across all Python evals
  language-requirements-js.md              # Shared across all JavaScript evals
  language-requirements-rs.md              # Shared across all Rust evals
```

At prompt assembly time the harness concatenates
`base-prompt.md` + `language-requirements-<lang>.md` + `technical-requirements-prompt.md`,
so each eval only needs to write the eval-specific parts.

Each eval's `conftest.py` re-exports fixtures from
`clispecbench.pytest_plugin` and declares an `EVAL_CONFIG` object
naming the task and its reference-implementation layout. Tests request
the `submission_command` fixture (a command sequence ready to splat into
`subprocess.run`) rather than a concrete executable path, which keeps
them language-agnostic. See `Evals/WordCount/tests/conftest.py` for a
minimal example.

If the eval should be runnable through `clispecbench`, register one task ID
per harness-visible `(eval, language)` pair in `src/clispecbench/harness/task.py`.
The current file uses `_register_language_tasks(...)`, and every registered
language is explicit, including `cpp`:

```python
_KNOWN_TASKS: dict[str, _RegisteredTask] = {
    **_register_language_tasks("mytask", "Evals/MyTask", ("cpp", "py")),
}
```

The reference implementation should pass all tests before committing. Verify:

```bash
pytest Evals/MyTask/tests --language=cpp -v
pytest Evals/MyTask/tests --language=py -v       # if a Python reference exists
```

### Versioning

Each eval has a `VERSION` file (semver) and a `CHANGELOG.md`. **Both must be
bumped on any change an agent or scoring run can observe.** That includes:

- Anything under `prompt/` — `base-prompt.md`, `technical-requirements-prompt.md`,
  or any file under `docs/`
- Anything under `tests/`
- The harness contract for this eval (CLI flags, exit codes, output schema)
- Reference implementations, when the change reflects a spec change rather
  than an internal refactor

Use semver:

- **Patch** (`1.0.0` → `1.0.1`) — clarifications, bug fixes, ambiguity
  resolutions that don't change what a correct submission looks like
- **Minor** (`1.0.1` → `1.1.0`) — new tests, expanded contract, additional
  requirements that previously passing submissions might still satisfy
- **Major** (`1.1.0` → `2.0.0`) — breaking changes; previously passing
  submissions may now fail

Pure refactors (renaming an internal helper, reformatting, restructuring a
reference impl without behavior change) do not need a bump. The harness
records `test_suite_version` from the git SHA on every run, but the per-eval
`VERSION` is what humans compare across results — keep them in sync, and
keep the changelog entry concrete enough that you could regenerate the diff
from the description.

### Prompt authoring guidelines

- `base-prompt.md` should describe the task from a domain expert perspective
  without engineering guidance. The agent should figure out the implementation.
- `technical-requirements-prompt.md` defines only what the harness needs to
  build and test, and should be **language-agnostic**: CLI flags, exit codes,
  output JSON schema. Do not put domain behavior or language-specific
  instructions here.
- `Evals/_shared/language-requirements-<lang>.md` holds the language-specific
  bits (target version, stdlib constraint, build/invoke command, source layout
  and entry point). These files are shared across all evals — only edit them
  when adding a new supported language or changing the harness contract for
  an existing one.
- `docs/` contains reference material the agent can use (specs, standards, etc.).

## Adding a Reference Implementation to an Existing Eval

This is an **eval-local** change. You are adding a reference implementation for
an existing eval in a language the repo already knows how to build and run.

1. **Write the reference implementation** at
   `Evals/<Task>/reference-implementation-<lang>/`. It must satisfy the CLI
   contract defined in that eval's `technical-requirements-prompt.md`.
2. **Update the eval's `conftest.py`** if you want
   `pytest Evals/<Task>/tests --language=<lang>` to find that reference
   implementation automatically when no `--implementation-root` is provided.
   In `EVAL_CONFIG`, add that language to `reference_impl_subdirs`.
3. **Run the hidden test suite** against it until it passes cleanly:
   ```bash
   pytest Evals/<Task>/tests --language=<lang>
   ```
4. **Do not change prompts or tests just because the language changed.**
   The hidden test suite is language-agnostic by construction.

Important distinction:

- Adding a reference implementation does **not** by itself create a new harness
  task.
- Adding a reference implementation also does **not** require new shared
  language support if `<lang>` is already supported by the harness.

Also note that an eval can still be tested against a supported language even if
it has no configured reference implementation for that language. In that case,
provide an explicit target with `--implementation-root` (or the eval-specific
environment variable used by `EVAL_CONFIG`).

## Exposing an Eval-Language Pair as a Harness Task

This is a **harness registration** change. Do this when you want an eval-language
pair to be invokable through:

- `clispecbench run --task ...`
- `clispecbench validate --task ...`

Add an entry to `_KNOWN_TASKS` in `src/clispecbench/harness/task.py`. By
convention, every task ID is suffixed with `-<lang>`, including `-cpp`:

```python
_KNOWN_TASKS: dict[str, _RegisteredTask] = {
    **_register_language_tasks("mytask", "Evals/MyTask", ("cpp", "py")),
}
```

This registration is about making a **task** visible to the harness CLI. It is
separate from adding a reference implementation. Pytest can still exercise an
explicit submission in a supported language via `--implementation-root` even if
no harness task ID exists for that eval-language pair.

## Adding a New Shared Evaluation Language

This is a **repo-wide language-support** change. Do this only when the harness
does not yet know how to build/run a language at all.

Required touchpoints:

1. Add a shared prompt at `Evals/_shared/language-requirements-<lang>.md`.
2. Add build/runtime support in `src/clispecbench/build/backends.py`.
3. Teach the shared pytest plugin about the language in
   `src/clispecbench/pytest_plugin.py`:
   - add it to `SUPPORTED_LANGUAGES`
   - add configured-reference lookup support in `_reference_impl_subdir_for_language()`
   - add backend selection support in `_build_backend_for()`
4. Add any required toolchain/runtime support to the host/docs and, if needed,
   `docker/base.Dockerfile`.

After that repo-wide support exists, you can separately choose whether to:

- add reference implementations for specific evals in that language
- expose specific eval-language pairs as harness tasks in `task.py`

## Linting and Formatting

This repository uses [Ruff](https://docs.astral.sh/ruff/) for linting and
formatting, and [Pyright](https://github.com/microsoft/pyright) for type
checking. Both are enforced in CI.

```bash
uv run ruff check          # lint
uv run ruff format         # format
uv run pyright             # type-check
```
