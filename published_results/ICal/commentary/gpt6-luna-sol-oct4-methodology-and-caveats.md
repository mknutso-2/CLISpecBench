# GPT-6 Luna and GPT-6 Sol — October 3–4, 2026

This publication contains 192 unique benchmark attempts: 96 for exact
`gpt-6-luna` and 96 for exact `gpt-6-sol`. Each model has one attempt per
eval/language/effort cell: eight evals, C++/Python/JavaScript/Rust, and
low/high/max. Isolated setup and availability probes are not benchmark rows.
GPT-6.1 Sol is a separate collection and is not part of this publication.

All 192 generations ended voluntarily, produced graded submissions,
and received substantive review of the full transcript/session/tool inventory,
source, failed cases, final claims, accounting, API-only audit, and worker
cleanup. There are no zero-score or operator-interrupted runs in this batch.
The editorial status `Incomplete` means the agent explicitly acknowledged
unfinished required coverage; it does not mean grading is unfinished. A
disclosed, permitted unsupported-calendar fallback alone does not imply that
status. `Complete` means a naturally
finished submission, not a claim that every hidden test passed. Per-run Last
Message summaries qualify the agent's claims against the observed result.

## Comparable frozen conditions

- Codex CLI 0.160.0, the same pinned local agent and grader images, and API-only
  networking; no successful external/reference acquisition was observed.
- Original benchmark input base: `f3e70a6ad1cf8ab2d2ae07ea3de79dc08e82474c`.
  Later recorded revisions include dashboard-only changes; the task inputs
  stayed frozen. Historical metadata and raw evidence have not been rewritten.
- Eval versions: RS274 3.2.2, WordCount 1.0.4, BibTeX 1.2.5, GEDCOM 4.0.3,
  ICal 3.0.5, IGES 1.0.21, LAS 2.0.5, and MARC21 3.0.2.
- The narrow Windows source-artifact-copy fix and exact-model pricing/accounting
  support were hash-pinned in the collection ledgers. No task prompt, hidden
  test, scoring, invocation, image, or per-container resource limit was changed.
- Model and effort were checked in canonical sessions. A null `served_model`
  field is not server-side model attestation and remains null.

Scores and per-test outcomes are the original frozen-suite observations, with
no regrading or adjustment. There is only one run per cell, so this batch does
not estimate within-cell variability. Comparisons across different historical
eval versions or network conditions require care.

## Accounting

Costs are standard-rate token estimates, not invoices or actual amounts paid.
Original token counts, cache accounting, tool definitions, and any unknown
fields are preserved. Sums of the stored, per-run rounded cost estimates are
$6.636970 for Luna and $147.350573 for Sol. Setup probes are excluded from these
totals. Eighteen Luna and four Sol runs have unavailable official tool counts;
those fields remain null, not zero. Scores are still available for those runs,
but tool-count-axis comparisons cannot include their unknown measurements.

For reference, the unweighted mean of the 32 individual task/language scores
at each effort is:

| Exact model | Low | High | Max |
| --- | ---: | ---: | ---: |
| gpt-6-luna | 58.711% | 68.177% | 87.894% |
| gpt-6-sol | 81.234% | 95.470% | 98.028% |

These means weight cells equally, not individual tests; eval suites have
different numbers of cases. The viewer's per-eval/language filters allow more
focused comparisons.

## Frozen ICal 3.0.5 limitations

The user chose to retain observed scores with these limitations documented,
and to defer any prompt/test repair to a future version. See the
[typed/raw and fixture adjudication note](https://github.com/mknutso-2/CLISpecBench/blob/main/docs/validation/non-rs274-2026-09-12/ical-valarm-publication-hold.md).

Some assertions require duplicate raw records for values already retained in
typed JSON fields, although that duplication policy is not unambiguously
specified. A raw-retention failure therefore does not automatically establish
missing alarm, attendee, period, relationship, or RSCALE capability. Actual
information loss must be distinguished from duplicate-storage expectations.

Other retained caveats concern the LOCATION-TYPE parameter fixture/citation
and a floating UNTIL in a positive VTIMEZONE fixture that the supplied RFC
requires to be UTC. Cell-specific reviews also record conflicting spring-gap
expectations between the summary and authoritative RFC. These caveats are
cell-specific, not an assertion that
all ICal failures are oracle defects. The per-run editorials distinguish
acknowledged gaps and observed implementation defects from these limitations.
No adjusted official scores are presented.

MARC21 per-run summaries identify mistaken rejections of documentation-permitted
values by submitted validators and limitations of their derived rule tables.
These are implementation findings, not a reason to adjust the observed scores.
Neither those findings nor the ICal caveats caused regeneration or rescoring.

Each published result's `metadata.run_uid` is the stable cross-reference to its
original, locally retained result and substantive review. Raw source files,
sessions, network audits, and credentials are not copied into the publication
tree. The local `artifacts` dictionary is removed; preserved original final
messages may still refer to files inside the agent's `/workspace`.
