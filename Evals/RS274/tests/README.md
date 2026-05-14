# RS274 Python Test Harness

These tests use `pytest` and are intended to target either:

- `Evals/RS274/reference-implementation-cpp/` (or `reference-implementation-py/`)
- an AI agent output directory supplied at runtime

## Usage

Run against the configured C++ reference implementation path:

```powershell
uv run pytest Evals/RS274/tests --language=cpp
```

Run against an agent output directory:

```powershell
uv run pytest Evals/RS274/tests --language=cpp --implementation-root C:\path\to\agent-output
```

Or point to a target with an environment variable:

```powershell
$env:CLISPECBENCH_RS274_ROOT = "C:\path\to\agent-output"
uv run pytest Evals/RS274/tests --language=cpp
```

If no buildable implementation exists at the configured reference path for the selected language, the build test is skipped with a clear message.

When adding or changing tests, keep the agent-facing prompt sources aligned with what the tests
assert:

- Put harness compatibility changes in `Evals/RS274/prompt/technical-requirements-prompt.md`.
- Put CNC/domain behavior requirements in `Evals/RS274/prompt/base-prompt.md` or
  `Evals/RS274/prompt/docs/`, not in `technical-requirements-prompt.md`.

When documenting why a test is valid:

- Cite the exact RS274 clause for each spec-invalid failure case.
- Require that each requirement-bearing test be grounded in behavior that is explicit and unambiguous in the RS274 text.
- If a proposed test depends on a nontrivial inference across multiple RS274 clauses, do not treat it as a requirement-bearing test unless the requirement is first clarified in non-RS274 eval docs such as `Evals/RS274/README.md` or `Evals/RS274/prompt/base-prompt.md`. Do not rely on changing `Evals/RS274/prompt/docs/RS274NGC.md` for this.
