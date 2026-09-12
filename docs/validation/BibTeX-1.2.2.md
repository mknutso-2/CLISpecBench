# BibTeX 1.2.2 validation — 2026-09-11

This is a hidden-test repair. `Evals/BibTeX/prompt/**` and the shared prompt
fragments are byte-identical to the pre-audit checkout. Existing saved source
can be fairly regraded; published generation observations are not rewritten.

The v1.2.1 changelog already identified an empty-entry fixture cascade. The
accepted `@misc{a}` syntax was a precondition of unrelated BST language,
output-buffer, sorting, Unicode, and state tests. Those fixtures now use
`@misc{a,}`; this keeps every field missing and therefore does not weaken
missing-field probes. One direct keys-only test retains comma-less empty-entry
coverage, derived from the supplied `bibtex.web` READ logic. No helper silently
repairs a submission's input or output. Response/log artifacts are removed
before each invocation to avoid stale-file credit.

Validation used Docker image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`,
with networking disabled, the repository mounted read-only, and a disposable
reference build. The C++ reference passes **376/376**. Test-suite hash:
`b1a15b70d4de75c7061bb22922d7880373fe49f1bdba612a47c390671692174d`.
Ruff and strict Pyright pass.

A controlled wrapper around the reference rejects only comma-less empty entries
whose keys are ordinary identifier tokens. Under v1.2.1 it passes 292/375 and
fails **83** cases; under v1.2.2 it passes 375/376 and fails **only the named
empty-entry syntax gate**. This measures removal of a real correlated
precondition, not hypothetical score improvement or deletion of that behavior.
The first exploratory wrapper also rejected quoted PREAMBLE values; it was
corrected before collecting these reported figures.

Some shared prerequisites remain unavoidable: a functioning CLI, executable
BST primitives, and observable output. Full reference-style parity cases are
intentional integration tests and can fail together from one primitive defect.
They should not be interpreted as counts of independent implementation bugs.
No old non-RS274 submission source was available locally during this audit;
these controls are reference/mutation runs, not historical model regrades.
