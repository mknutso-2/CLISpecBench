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

## Probe Coverage TODO

- [x] Add a `G21` probing case that proves the inch-defined `--probe-box` extents are interpreted correctly after unit conversion.
- [x] Add explicit success-path checks for probe-result parameters `5064` through `5066`.
- [ ] Decide whether any additional probe/tool validation cross-product cases add meaningful coverage beyond the current wrong-tool, spindle-on, already-tripped, and no-hit matrices.
