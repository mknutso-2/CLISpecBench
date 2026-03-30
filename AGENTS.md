This repo stores the implementation for a new software engineering benchmark. To start, it contains code for only a single eval in the benchmark called CNCSim.

Contents:
- SWE-BuildBench-Design.md contains the proposed benchmark-level design.
- CNCSim/CNCSim-Design.md contains the CNCSim-specific eval design. This design doc mentions a full and lite version of the eval. We're currently working on just the full version.
- CNCSim/tests/ contains the CNCSim tests run against the implementation written during the eval (or on the "reference" implementation)
- CNCSim/prompt/base-prompt.md is the 'non-technical' prompt presented to the AI coding agent.
- CNCSim/prompt/technical-requirements-prompt.md is the harness-compatibility prompt presented to the AI coding agent. It should contain only requirements the harness needs in order to build, invoke, and read results from the submission: language/tooling constraints, CLI flags, exit codes, and output schema/serialization details. **Update this document only when the harness contract changes. Do not add CNC/domain behavior here just because tests assert it; behavioral requirements belong in base-prompt.md and the docs/ folder. If a new test depends on behavior that is not derivable from those sources, fix those sources rather than technical-requirements-prompt.md. Agents must be able to, theoretically, pass every test in the suite using only base-prompt.md, technical-requirements-prompt.md, and the docs/ folder.**
- CNCSim/prompt/docs/RS274NGC.md contains the RS274 documentation converted to markdown. **Do not edit files in this folder unless explicitly asked to do so.**
- CNCSim/reference-implementation/ contains a running reference implementation of the eval. At each commit, it should contain an implementation that passes all the tests in the eval.

Test-authoring rule for CNCSim:
- The RS274 spec is the source of truth, and tests should only enforce behavior that is explicit and unambiguous in that document. If a proposed test depends on a nontrivial inference across multiple clauses rather than a plainly stated requirement, do not add it as a requirement-bearing test. Instead, either leave it untested or first clarify the requirement in non-RS274 eval docs such as `CNCSim/CNCSim-Design.md` or `CNCSim/prompt/base-prompt.md`. Do not rely on changing `CNCSim/prompt/docs/RS274NGC.md` for this.

Agent workflow note:
- `.vscode/settings.json` save actions are only applied by VS Code during editor saves. They are not automatically applied to files created or modified by AI agents via patches, shell commands, scripts, or other direct filesystem writes.
- When editing Python files, run Ruff and Pyright explicitly as needed instead of assuming editor integrations will format code, fix lint issues, organize imports, or catch type-checking issues. `pyproject.toml` enables strict Pyright checking for both `src` and `CNCSim/tests`, so Python test changes should be verified with Pyright too, not just Ruff and pytest.
- For Python packages, keep `__init__.py` minimal. Do not re-export module-level constants, helpers, or other names from the package root unless they are intentionally part of a stable public API. Prefer importing from the defining module directly.
- Before concluding any task and reporting completion, always invoke the `claude-critique` skill against the changes you made. Point Claude at the exact diff, commit, or files under review, and continue the review until you and Claude agree that the changes have been cross-validated.
- If you and Claude do not agree, do not silently pick one opinion and move on. Create `ARGUMENT.md` at the repo root that records both positions, the relevant files or spec passages, and the unresolved disagreement.
