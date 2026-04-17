# SWE-BuildBench

A benchmark suite for evaluating AI coding agents on documentation-driven
implementation tasks. Agents receive a specification and domain docs, then must
produce a working implementation that passes a hidden test suite. Tasks may
expose one or more target languages; the harness currently supports C++,
Python, JavaScript, and Rust, with a shared test suite verifying each
submission through a language-agnostic CLI contract.

## Repository Layout

```
Evals/                   # Evaluation tasks (one directory per task)
  _shared/               #   Shared language-requirements prompts
  CNCSim/                #   CNC G-code interpreter (full benchmark task)
  IGES/                  #   IGES CAD interchange parser/writer eval
  IGES-SDK/              #   Upstream IGES porting source tree
  WordCount/             #   Word frequency counter (toy eval for harness testing)
src/swe_buildbench/      # Python package: harness, agent adapters, shared build utils
docker/                  # Dockerfiles (base image + per-agent images)
scripts/                 # Setup and utility scripts
```

Design docs:

- `Eval-Design.md` -- benchmark-level design (scoring, task anatomy, eval modes)
- `Harness-Design.md` -- evaluation harness architecture and implementation
- `Evals/CNCSim/README.md` -- CNCSim task design and test categories
- `Evals/IGES/README.md` -- IGES eval design, scope, and contract notes

## Requirements

Requirements depend on what you plan to do on the **host machine**:

- **Always needed on the host**
  - **Python 3.11+** with [uv](https://docs.astral.sh/uv/) (or pip) — needed to
    install dependencies, run `swe-buildbench`, and run the pure-Python test suite.
  - **Docker Engine** in WSL2 (Windows) or native Docker (Linux/macOS) — needed for
    normal `swe-buildbench run` usage, container smoke tests, auth smoke tests, and
    any workflow that uses the sandbox images.
- **Needed on the host only for local reference-implementation workflows**
  - **CMake + a C++ compiler** — needed if you run C++ reference implementations or
    point tests at a local C++ submission with `--implementation-root`.
    - **C++20** is the shared prompt/harness baseline and is sufficient for the current
      `CNCSim` and `WordCount` C++ reference implementations.
    - **C++23-capable compiler** is needed if you also want to build/run the current
      `IGES` C++ reference implementation.
  - **Node.js 22+** — needed only if you run JavaScript reference implementations on
    the host, such as `pytest Evals/WordCount/tests --language=js` or
    `pytest Evals/CNCSim/tests --language=js`.
  - **Rust stable** via [rustup](https://rustup.rs/) — needed only if you run Rust
    reference implementations on the host, such as
    `pytest Evals/WordCount/tests --language=rs` or `pytest Evals/CNCSim/tests --language=rs`.
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
bash /mnt/c/Git/SWE-BuildBench/scripts/install-docker-wsl.sh
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

This creates `swe-buildbench-base:latest` (Ubuntu 24.04, CMake, g++-14, pytest)
and CLI agent images (`swe-buildbench-claude-code`,
`swe-buildbench-codex-cli`, `swe-buildbench-copilot-cli`,
`swe-buildbench-gemini-cli`) that extend it.

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
  invoke `swe-buildbench`. Credentials in `~/.claude/`, `~/.codex/`,
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
swe-buildbench run --task iges --agent copilot-cli
```

View results:

```bash
swe-buildbench results
```

## Running Tests

This project has four categories of tests. CI runs the first three on
every PR; the fourth is a hand-run diagnostic for new-machine setup.

| Category                                                  | Location                                       | Runner   | Cost                | Prereqs                              |
|-----------------------------------------------------------|------------------------------------------------|----------|---------------------|--------------------------------------|
| [**Eval reference tests**](#eval-reference-tests)         | `Evals/<task>/tests/`                          | `pytest` | No API cost         | C++ toolchain                        |
| [**Harness unit tests**](#harness-tests)                  | `src/swe_buildbench/tests/` (unmarked)         | `pytest` | No API cost         | `uv sync`                            |
| [**Container smoke tests**](#harness-tests)               | `src/swe_buildbench/tests/` (`docker` marker)  | `pytest` | No API cost         | Docker daemon + built images         |
| [**Auth smoke tests**](#auth-smoke-tests)                 | `scripts/smoke-test-*.sh`                      | bash     | ~pennies of tokens  | Docker + agent creds + built images  |

### Eval reference tests

Each task's hidden test suite, run against its reference implementation:

```bash
pytest Evals/CNCSim/tests
pytest Evals/IGES/tests
pytest Evals/WordCount/tests
```

Select a target language (when multiple reference implementations exist):

```bash
pytest Evals/WordCount/tests --language=py
pytest Evals/WordCount/tests --language=js
pytest Evals/WordCount/tests --language=rs
pytest Evals/WordCount/tests --language=cpp       # default
```

Point tests at a different implementation (e.g. an agent's output):

```bash
pytest Evals/WordCount/tests --implementation-root /path/to/agent-output
pytest Evals/WordCount/tests --language=py --implementation-root /path/to/py-output
```

### Harness tests

The harness has its own pytest suite under `src/swe_buildbench/tests/`.
Tests are tagged with markers so you can pick a subset:

| Marker          | Meaning                                                      |
|-----------------|--------------------------------------------------------------|
| (unmarked)      | Pure-Python unit tests -- no Docker, no API calls            |
| `docker`        | Spins up real containers; needs Docker daemon + built images |
| `prompts_agent` | Sends a real prompt to an AI coding agent (consumes tokens)  |

Typical filters (mirror what CI runs):

```bash
# Fast unit tests only -- CI's `unit-tests` job
uv run pytest src/swe_buildbench/tests -m "not docker and not prompts_agent"

# Container smoke tests -- CI's `container-tests` job
# (requires built images -- see "Build Docker images" in Environment Setup)
uv run pytest src/swe_buildbench/tests -m "docker and not prompts_agent"

# Everything that doesn't cost API tokens
uv run pytest src/swe_buildbench/tests -m "not prompts_agent"
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
DOCKER_HOST=tcp://localhost:2375 uv run pytest src/swe_buildbench/tests -m "docker and not prompts_agent"
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

## Adding a New Eval

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
  reference-implementation-cpp/            # C++ reference (default language)
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
`swe_buildbench.pytest_plugin` and declares an `EVAL_CONFIG` object
naming the task and its reference-implementation layout. Tests request
the `submission_command` fixture (a command sequence ready to splat into
`subprocess.run`) rather than a concrete executable path, which keeps
them language-agnostic. See `Evals/WordCount/tests/conftest.py` for a
minimal example.

Register the task in `src/swe_buildbench/harness/task.py`. Register one task
ID per (eval, language) pair — the default language is `cpp`, and additional
languages take an explicit `language=` kwarg:

```python
_KNOWN_TASKS: dict[str, _RegisteredTask] = {
    ...
    "mytask": _RegisteredTask("Evals/MyTask"),
    "mytask-py": _RegisteredTask("Evals/MyTask", language="py"),
}
```

The reference implementation should pass all tests before committing. Verify:

```bash
pytest Evals/MyTask/tests -v
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

## Adding a Language Variant to an Existing Eval

Once an eval has a working reference implementation in at least one language,
adding a new language variant reuses the existing prompt, documentation corpus,
and hidden test suite — only a new reference implementation and a task-registry
entry are required.

Prerequisites (one-time per language, across the whole repo):

1. `Evals/_shared/language-requirements-<lang>.md` exists. If not, create it —
   it should state the target language version, stdlib-only constraint,
   build/invoke command template, and source layout / entry-point convention.
2. `src/swe_buildbench/build/backends.py` has a `BuildBackend` implementation
   for `<lang>` and `LanguageTarget.missing_requirements()` recognizes it.
3. `docker/base.Dockerfile` installs the compiler/runtime.

Per-eval steps to add a new language variant:

1. **Write the reference implementation** at
   `Evals/<Task>/reference-implementation-<lang>/`. It must satisfy the CLI
   contract defined in that eval's `technical-requirements-prompt.md`.
2. **Run the hidden test suite** against it until it passes cleanly:
   ```bash
   pytest Evals/<Task>/tests --language=<lang>
   ```
   The `--language=<lang>` flag tells the shared pytest plugin to build and
   invoke the `reference-implementation-<lang>/` directory via the matching
   `BuildBackend`. If any tests fail, the reference implementation is wrong
   (or, rarely, the test is ambiguous — see AGENTS.md for the cross-validation
   protocol).
3. **Register a new task ID** in `src/swe_buildbench/harness/task.py` by
   adding a `_RegisteredTask(..., language="<lang>")` entry alongside the
   existing cpp one. By convention, suffix the task ID with `-<lang>` (e.g.
   `cncsim-full` → `cncsim-full-py`).
4. **Validate the registration**:
   ```bash
   swe-buildbench validate --task <task-id>-<lang>
   ```
   This prints the resolved base / language / technical prompt paths and
   confirms the language prompt exists. The eval's `base-prompt.md`,
   `technical-requirements-prompt.md`, `docs/`, and `tests/` are unchanged;
   do not fork them per language.

That's it — no test code, prompt edits, or CLI changes are needed. The
hidden test suite is language-agnostic by construction (it calls the
`submission_command` fixture rather than a concrete executable path), so the
same tests that validated the cpp reference now validate the new language
variant end-to-end.

## Linting and Formatting

This repository uses [Ruff](https://docs.astral.sh/ruff/) for linting and
formatting, and [Pyright](https://github.com/microsoft/pyright) for type
checking. Both are enforced in CI.

```bash
uv run ruff check          # lint
uv run ruff format         # format
uv run pyright             # type-check
```
