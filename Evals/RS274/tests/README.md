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

The shared runners take a program **body** and add balanced percent delimiters
as required by RS274 section 3.1. This avoids the unresolved bare-EOF behavior
without inserting M2/M30 resets. Use `input_line(body_line)` for trace assertions
to refer to the actual submitted file's physical line; never rewrite a
submission's returned line numbers. Delimiter tests write raw complete files
and bypass this wrapper. Parsing the file and producing an observable JSON
result remain fundamental prerequisites, identified by dedicated gates.

When adding or changing tests, keep the agent-facing prompt sources aligned with what the tests
assert:

- Put harness compatibility changes in `Evals/RS274/prompt/technical-requirements-prompt.md`.
- Put CNC/domain behavior requirements in `Evals/RS274/prompt/base-prompt.md` or
  `Evals/RS274/prompt/docs/`, not in `technical-requirements-prompt.md`.

When documenting why a test is valid:

- Cite the exact RS274 clause for each spec-invalid failure case.
- Require that each requirement-bearing test be grounded in behavior that is explicit and unambiguous in the RS274 text.
- If a proposed test depends on an ambiguous inference, clarify the behavior in
  the agent-visible `prompt/base-prompt.md` or `prompt/docs/Clarifications.md`
  before requiring it. This maintainer README and `Evals/RS274/README.md` are
  not model inputs and cannot establish a behavioral requirement. Use the
  technical prompt only for CLI/output-contract clarifications; preserve the
  `RS274NGC.md` mirror. Any such change needs its version/changelog update.
- Isolate behavioral checks from unrelated setup and output-schema details.
  Dedicated schema tests own shape requirements. Negative-input cases should
  contain only the intended invalid condition, with otherwise valid fixtures.
