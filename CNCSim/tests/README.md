# CNCSim Python Test Harness

These tests use `pytest` and are intended to target either:

- `CNCSim/reference-implementation/`
- an AI agent output directory supplied at runtime

## Usage

Run against the default reference implementation path:

```powershell
uv run pytest CNCSim/tests
```

Run against an agent output directory:

```powershell
uv run pytest CNCSim/tests --implementation-root C:\path\to\agent-output
```

Or point to a target with an environment variable:

```powershell
$env:SWEBUILDBENCH_IMPLEMENTATION_ROOT = "C:\path\to\agent-output"
uv run pytest CNCSim/tests
```

If no buildable implementation exists at the default location, the build test is skipped with a clear message.

When adding or changing tests, keep the agent-facing prompt sources aligned with what the tests
assert:

- Put harness compatibility changes in `CNCSim/prompt/technical-requirements-prompt.md`.
- Put CNC/domain behavior requirements in `CNCSim/prompt/base-prompt.md` or
  `CNCSim/prompt/docs/`, not in `technical-requirements-prompt.md`.

When documenting why a test is valid:

- Cite the exact RS274 clause for each spec-invalid failure case.
- Require that each requirement-bearing test be grounded in behavior that is explicit and unambiguous in the RS274 text.
- If a proposed test depends on a nontrivial inference across multiple RS274 clauses, do not treat it as a requirement-bearing test unless the requirement is first clarified in non-RS274 eval docs such as `CNCSim/CNCSim-Design.md` or `CNCSim/prompt/base-prompt.md`. Do not rely on changing `CNCSim/prompt/docs/RS274NGC.md` for this.

## Parameter/Expression Coverage TODOs

- [x] Add explicit parameter/expression coverage for arc `I`/`J`/`K`/`R` words.
- [x] Broaden G-word parameter/expression coverage beyond the current sampled cases to include modal groups such as `G17`/`G18`/`G19`, `G90`/`G91`, `G20`/`G21`, and `G93`/`G94`.
- [ ] Add explicit unary-operation or repeated-`#` coverage outside axis words, such as in `F`, `S`, `T`, `H`, `D`, or arc words.
