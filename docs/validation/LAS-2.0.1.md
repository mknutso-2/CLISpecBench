# LAS 2.0.1 scoring audit — 2026-09-11

This patch changes tests only. `prompt/` and shared language inputs are unchanged.
The preceding suite contained 220 cases; the corrected suite has 219.

## Corrections and public basis

- The response contract distinguishes invalid input (exit 1) from internal failure
  (exit 2). The old `_was_rejected` accepted **any nonzero exit**, crediting an
  immediately crashing executable for every validation case. A rejection now
  needs JSON with an error indication and cannot be an internal-error response.
  Either `status: error` or a nonempty `error` suffices; exact envelope/schema and
  error-code routing remain in `test_schema.py`.
- The JSON contract lists the fields used by each point format but does not
  specify rejection of additional keys. Removed the requirement to reject an
  otherwise valid format-0 render request containing a color key. Existing
  format-layout tests still require correct serialized point bytes.
- The LAS corpus defines extrema from the point data but does not define the
  extrema of an empty point list. The empty-render case now excludes just the
  six binary min/max doubles from byte comparison. Header completeness,
  counters, offsets, VLRs and the other emitted bytes still have to match.
- A repeated success `status` assertion was removed from format behavior checks;
  response-schema tests own it. Prior response files are cleared before an
  invocation, so repeated calls cannot reuse stale output.

## Validation

Pinned grader image:
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`.
Containers mount the repository read-only and run with `--network none`.

- Unmodified Python reference, preceding tests: **220/220**.
- Unmodified Python reference, corrected tests: **219/219** (also repeated on the host).
- Deliberately broken Python submission that immediately exits 1 without output:
  **0/219**, including **0 validation passes**. The preceding helper accepted
  that process failure as rejection.
- Ruff and strict Pyright pass for both corrected engineering test directories.

The full raw reports and test mutation drivers were captured in the workstation's
`work/engineering-audit/` scratch directory. These are reference/mutation checks,
not inference runs or new published model scores. No old non-RS274 generated
sources were available on this workstation for fair rescoring.

## Limits and future public clarification

An explicit policy for unknown render JSON keys and empty-dataset extrema would
be a model-visible contract change; neither policy is retroactively imposed.
A program deliberately rejecting all requests can still pass rejection-only
cases, while failing positive cases. Likewise fundamental inability to decode
LAS or JSON remains a shared prerequisite. A score counts passed tests, not
statistically independent implementation defects; the changes do not establish
that coverage is complete or that the suite is unsaturated.
