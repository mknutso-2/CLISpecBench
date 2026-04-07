This repo stores the implementation for a new software engineering benchmark. To start, it contains code for only a single eval in the benchmark called CNCSim.

Contents:
- SWE-BuildBench-Design.md contains the proposed benchmark-level design.
- Evals/CNCSim/CNCSim-Design.md contains the CNCSim-specific eval design. This design doc mentions a full and lite version of the eval. We're currently working on just the full version.
- Evals/CNCSim/tests/ contains the CNCSim tests run against the implementation written during the eval (or on the "reference" implementation)
- Evals/CNCSim/prompt/base-prompt.md is the 'non-technical' prompt presented to the AI coding agent.
- Evals/CNCSim/prompt/technical-requirements-prompt.md is the harness-compatibility prompt presented to the AI coding agent. It should contain only requirements the harness needs in order to build, invoke, and read results from the submission: language/tooling constraints, CLI flags, exit codes, and output schema/serialization details. **Update this document only when the harness contract changes. Do not add CNC/domain behavior here just because tests assert it; behavioral requirements belong in base-prompt.md and the docs/ folder. If a new test depends on behavior that is not derivable from those sources, fix those sources rather than technical-requirements-prompt.md. Agents must be able to, theoretically, pass every test in the suite using only base-prompt.md, technical-requirements-prompt.md, and the docs/ folder.**
- Evals/CNCSim/prompt/docs/RS274NGC.md contains the RS274 documentation converted to markdown. **Do not edit files in this folder unless explicitly asked to do so.**
- Evals/CNCSim/reference-implementation/ contains a running reference implementation of the eval. At each commit, it should contain an implementation that passes all the tests in the eval.

Test-authoring rule for CNCSim:
- The RS274 spec is the source of truth, and tests should only enforce behavior that is explicit and unambiguous in that document. If a proposed test depends on a nontrivial inference across multiple clauses rather than a plainly stated requirement, do not add it as a requirement-bearing test. Instead, either leave it untested or first clarify the requirement in non-RS274 eval docs such as `Evals/CNCSim/CNCSim-Design.md` or `Evals/CNCSim/prompt/base-prompt.md`. Do not rely on changing `Evals/CNCSim/prompt/docs/RS274NGC.md` for this.

Agent workflow note:
- `.vscode/settings.json` save actions are only applied by VS Code during editor saves. They are not automatically applied to files created or modified by AI agents via patches, shell commands, scripts, or other direct filesystem writes.
- When editing Python files, run Ruff and Pyright explicitly as needed instead of assuming editor integrations will format code, fix lint issues, organize imports, or catch type-checking issues. `pyproject.toml` enables strict Pyright checking for both `src` and `Evals/CNCSim/tests`, so Python test changes should be verified with Pyright too, not just Ruff and pytest.
- For Python packages, keep `__init__.py` minimal. Do not re-export module-level constants, helpers, or other names from the package root unless they are intentionally part of a stable public API. Prefer importing from the defining module directly.

Cross-validation requirement (applies to all agents):
- Before concluding any task and reporting completion, the agent must obtain adversarial cross-validation from a different AI system (see agent-specific sections below). Point the reviewer at the exact diff, commit, or files under review, and continue the review until the two agents agree that the changes have been cross-validated.
- This cross-validation requirement also applies to analysis and synthesis tasks, not just code changes. If the reviewing agent produced findings and you plan to omit, downgrade, reject, or contradict any of them in your response to the user, first do a targeted follow-up review on those exact points.
- When relaying cross-validation output, explicitly distinguish between:
  - the full superset of findings that were raised
  - the narrower consensus list you believe remains after reconciliation
  - findings rejected as stale, incorrect, already covered, or unobservable under the current harness
- If you and the reviewing agent do not agree, do not silently pick one opinion and move on. Create `ARGUMENT.md` at the repo root that records both positions, the relevant files or spec passages, and the unresolved disagreement.
- If the reviewing agent is unavailable, rate-limited, or otherwise cannot complete the needed reconciliation round, create `ARGUMENT.md` before answering and say that the disagreement remains unresolved due to that limitation.

### Cross Validation

Use the `claude-critique` skill to invoke Claude as the adversarial reviewer. Point Claude at the exact diff, commit, or files under review using the workflow and prompt templates documented in that skill. Use named sessions (`--conversation <label>`) so multi-round review exchanges are preserved as readable transcripts in `claude-conversations/`.

**Important:** When Codex is running as a subagent invoked by Claude (e.g. via `/codex:rescue` or `/codex:adversarial-review`), it must **not** use the `claude-critique` skill. The Codex sandbox cannot spawn the Claude CLI (EPERM), and even if it could, the review would be redundant — Claude is already the orchestrating agent and will handle reconciliation directly. The `claude-critique` skill is only for use when Codex is the top-level primary agent driving the session.

Workflow:
1. Before calling the review, prepare the review target (working-tree changes, a commit hash, or specific files).
2. Invoke `/codex:adversarial-review` with a focus prompt that includes:
   - what code to inspect (e.g. "Review the working-tree changes" or "Review commit abc1234")
   - which docs define correctness (e.g. AGENTS.md, CNCSim-Design.md, base-prompt.md, RS274NGC.md)
   - the instruction to be skeptical and surface concrete findings with file references
3. Codex's review output is returned verbatim into the Claude Code conversation, so the user can see the full exchange.
4. Evaluate Codex's findings. For each finding, either accept it and fix the issue, or prepare a counterargument grounded in the spec/code.
5. If findings remain disputed after one follow-up round, create `ARGUMENT.md` as described above.

Example invocation:
```
/codex:adversarial-review Review the working-tree changes. Check alignment with AGENTS.md, Evals/CNCSim/CNCSim-Design.md, Evals/CNCSim/prompt/base-prompt.md, Evals/CNCSim/prompt/technical-requirements-prompt.md, and the RS274 docs. Be skeptical. Focus on concrete findings with file references, not style.
```
