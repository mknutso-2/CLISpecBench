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
