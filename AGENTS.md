This repo stores the implementation for a new software engineering benchmark. To start, it contains code for only a single eval in the benchmark called CNCSim.

Contents:
- Eval-Design.md contains the proposed benchmark-level design.
- Evals/CNCSim/CNCSim-Design.md contains the CNCSim-specific eval design. This design doc mentions a full and lite version of the eval. We're currently working on just the full version.
- Evals/CNCSim/tests/ contains the CNCSim tests run against the implementation written during the eval (or on the "reference" implementation)
- Evals/CNCSim/prompt/base-prompt.md is the 'non-technical' prompt presented to the AI coding agent.
- Evals/CNCSim/prompt/technical-requirements-prompt.md is the harness-compatibility prompt presented to the AI coding agent. It should contain only requirements the harness needs in order to build, invoke, and read results from the submission: language/tooling constraints, CLI flags, exit codes, and output schema/serialization details. **Update this document only when the harness contract changes. Do not add CNC/domain behavior here just because tests assert it; behavioral requirements belong in base-prompt.md and the docs/ folder. If a new test depends on behavior that is not derivable from those sources, fix those sources rather than technical-requirements-prompt.md. Agents must be able to, theoretically, pass every test in the suite using only base-prompt.md, technical-requirements-prompt.md, and the docs/ folder.**
- Evals/CNCSim/prompt/docs/RS274NGC.md contains the RS274 documentation converted to markdown. **Do not edit files in this folder unless explicitly asked to do so.**
- Evals/CNCSim/reference-implementation-cpp/ (C++) and Evals/CNCSim/reference-implementation-py/ (Python) contain running reference implementations of the eval. At each commit, each should contain an implementation that passes all the tests in the eval for its language.

Test-authoring rules:
- The RS274 spec is the source of truth, and tests should only enforce behavior that is explicit and unambiguous in that document. If a proposed test depends on a nontrivial inference across multiple clauses rather than a plainly stated requirement, do not add it as a requirement-bearing test. Instead, either leave it untested or first clarify the requirement in non-RS274 eval docs such as `Evals/CNCSim/CNCSim-Design.md` or `Evals/CNCSim/prompt/base-prompt.md`. Do not rely on changing `Evals/CNCSim/prompt/docs/RS274NGC.md` for this.
- **Every bug found in a reference implementation must have a corresponding eval test.** Reference implementations exist to validate the test suite, not the other way around. When a bug is discovered in a ref impl — whether by code review, Codex/subagent critique, or manual testing — fix the ref impl AND add or update a test in the eval's `tests/` directory that would catch the incorrect behavior. The test enforces the correct behavior on agent submissions; without it, the bug fix is invisible to the benchmark.

Agent workflow note:
- `.vscode/settings.json` save actions are only applied by VS Code during editor saves. They are not automatically applied to files created or modified by AI agents via patches, shell commands, scripts, or other direct filesystem writes.
- When editing Python files, run Ruff and Pyright explicitly as needed instead of assuming editor integrations will format code, fix lint issues, organize imports, or catch type-checking issues. `pyproject.toml` enables strict Pyright checking for both `src` and `Evals/CNCSim/tests`, so Python test changes should be verified with Pyright too, not just Ruff and pytest.
- For Python packages, keep `__init__.py` minimal. Do not re-export module-level constants, helpers, or other names from the package root unless they are intentionally part of a stable public API. Prefer importing from the defining module directly.
- **Bump per-eval `VERSION` + `CHANGELOG.md` on any contract-affecting change.** Each `Evals/<Task>/` has a `VERSION` file (semver) and a `CHANGELOG.md`. Bump both whenever you change anything an agent or scoring run can observe: prompt files (`base-prompt.md`, `technical-requirements-prompt.md`, `docs/`), `tests/`, the harness contract (CLI flags, exit codes, output schema), or reference implementations in a way that reflects a spec change. Patch bump for clarifications and bug fixes; minor for new behavior or expanded contract; major for breaking changes. Pure refactors that don't change observable behavior do not need a bump. See README.md → "Versioning" for the canonical version of this rule.

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

### Post-Run Log Inspection (required for all eval runs)

After every eval run completes, the agent operating the harness **must** inspect the result and transcript before moving on to the next run. Do not batch up runs and inspect later — inspect each one as it finishes. The `metadata.notes` field in the result JSON exists for recording these observations.

**For every run that scores 0/N (zero tests passed):**

Open the transcript (`transcript.jsonl` in the run directory) and determine the root cause. Classify it as one of:

- **timeout**: Agent was still actively working when killed. Note whether it had written any source files and whether they were buildable.
- **auth_failure**: Agent logs show 401/403 errors, expired tokens, or credential problems. The agent never started real work.
- **rate_limit**: Agent logs show 429 errors or quota exhaustion from the model API.
- **context_exhausted**: Agent hit context window limits (e.g. `context_length_exceeded`). Note how far it got.
- **no_code_written**: Agent completed voluntarily (`end_turn` / `exit_code=0`) but never wrote source files. Check if it only planned/analyzed without implementing.
- **build_failure**: Agent wrote source but it doesn't compile. Check build diagnostics.
- **agent_error**: Agent crashed, threw an unhandled exception, or encountered an internal error.
- **model_error**: The backing model API returned errors unrelated to auth/rate limits (e.g. server errors, capacity issues).

Record the classification and a brief explanation in the result JSON's `metadata.notes` field, or if the harness has already written the file, note it in your report to the user.

**For every run that scores > 0:**

Confirm from the transcript that the agent acknowledged it was done working. Specifically check:
- Did the agent voluntarily exit / signal completion? (Good — this is a clean run.)
- Was the agent still actively working when the timeout killed it? (The score is valid but the agent might have scored higher with more time — note this.)
- Did the agent ask for user input or clarification but get no response because we weren't running interactively? (This is a harness problem — note it.)
- Did the agent hit a rate limit or error partway through but had already written enough code to pass some tests? (Partial result — note it.)

**Report format:**

When presenting results to the user, always include:
1. The language/task variant used (e.g. `cncsim-full` = C++, `cncsim-full-py` = Python)
2. For each zero-score run: the root cause category and a one-line explanation
3. For non-zero runs that timed out: note that the score may be artificially low
4. Any infrastructure issues discovered (auth problems, rate limits, etc.) that invalidate results and require reruns
