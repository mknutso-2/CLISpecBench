<!-- This text can be inserted into AGENTS.md when you want to attempt to force
Codex to ask claude to critique its work. -->
## Cross-validation requirement

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

**Important:** When Codex is running as a subagent invoked by Claude (for example via `/codex:rescue` or `/codex:adversarial-review`), it must **not** use the `claude-critique` skill. The Codex sandbox cannot spawn the Claude CLI (`EPERM`), and even if it could, the review would be redundant because Claude is already the orchestrating agent and will handle reconciliation directly. The `claude-critique` skill is only for use when Codex is the top-level primary agent driving the session.

Workflow:
1. Before calling the review, prepare the review target (working-tree changes, a commit hash, or specific files).
2. Invoke `/codex:adversarial-review` with a focus prompt that includes:
   - what code to inspect (for example "Review the working-tree changes" or "Review commit abc1234")
  - which docs define correctness (for example `AGENTS.md`, `Evals/RS274/README.md`, `Evals/RS274/prompt/base-prompt.md`, `Evals/RS274/prompt/technical-requirements-prompt.md`, and the RS274 docs)
   - the instruction to be skeptical and surface concrete findings with file references
3. Codex's review output is returned verbatim into the Claude Code conversation, so the user can see the full exchange.
4. Evaluate Codex's findings. For each finding, either accept it and fix the issue, or prepare a counterargument grounded in the spec or code.
5. If findings remain disputed after one follow-up round, create `ARGUMENT.md` as described above.

Example invocation:
```text
/codex:adversarial-review Review the working-tree changes. Check alignment with AGENTS.md, Evals/RS274/README.md, Evals/RS274/prompt/base-prompt.md, Evals/RS274/prompt/technical-requirements-prompt.md, and the RS274 docs. Be skeptical. Focus on concrete findings with file references, not style.
```
