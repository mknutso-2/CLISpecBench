# SWE-BuildBench

Design docs:

- `SWE-BuildBench-Design.md` for benchmark-level design
- `CNCSim/CNCSim-Design.md` for the CNCSim-specific task design

## Prompt Scope

For CNCSim, behavioral CNC requirements belong in `CNCSim/prompt/base-prompt.md` and
`CNCSim/prompt/docs/`. `CNCSim/prompt/technical-requirements-prompt.md` is reserved for the
test harness contract only: language/tooling constraints, CLI flags, exit codes, and output
schema/serialization details.

## Line Endings

This repository enforces LF line endings via `.gitattributes`.

On Windows, keep Git configured for LF-friendly behavior:

```powershell
git config --global core.autocrlf false
git config --global core.safecrlf true
```
