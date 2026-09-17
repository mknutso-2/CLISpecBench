# Non-RS274 scoring audit and GPT coverage

Checkpoint: 2026-09-17T04:41:02.469789+00:00. Local implementation revision `9319ef28e5ff38598db7b687de3dde38048063c0`. Results are in the local publication tree; no push has been made for this task.

The user resumed work on September 16 with one submission at a time: finish each retained review before new generation, then finish and review each new run before starting another. The previous parallel queue remains disabled. See the [resume instructions](../../operations/Non-RS274-Audit-Resume.md).

All seven other tasks contained scoring weaknesses: invalid fixtures, unsupported hidden restrictions, missing focused coverage, or failure amplification. Fixes keep every assembled model input unchanged across all 28 task/language combinations. Patch versions, dated changelogs, public-spec comments and per-task validation records accompany the changes. Public prose ambiguities that cannot be resolved under its existing precedence or explicit permissions are deferred to a separate public-input revision.

| Task | Final version | Principal repair | Validation record |
|---|---|---|---|
| WordCount |1.0.4| Byte/line/delimiter boundaries, frequency ranking, JSON and CLI coverage; C++ reference fixes.|[WordCount](../WordCount-1.0.4.md)|
| LAS |2.0.4| Do not reward internal errors; valid waveform offsets, permitted representations, explicit short ExtraBytes tail and a storage contradiction independent of a deprecated bit.|[LAS](../LAS-2.0.4.md)|
| GEDCOM |4.0.3| Optional cross-reference IDs, reciprocal family contexts, focused backlink negatives and an isolated void-pointer case.|[GEDCOM](../GEDCOM-4.0.3.md)|
| MARC21 |3.0.2| Remove universal skip gates; repair fixed fields, currency/linkage examples and valid ordering contexts; leave ambiguous minima unscored.|[MARC21](../MARC21-3.0.2.md)|
| BibTeX |1.2.4| Valid BST/stack fixtures, independent oracle goldens, explicit approximation allowances and corrected past-end name selection.|[BibTeX](../BibTeX-1.2.4.md)|
| iCalendar |3.0.2| Defined recurrence sets, valid timezone/component/method fixtures and permitted representations.|[ICal](../ICal-3.0.2.md)|
| IGES |1.0.17| Legal shared Global data and typed reference graphs; independent Hollerith validation and focused semantic controls.|[IGES](../IGES-1.0.17.md)|

Failure amplification was material. One illegal shared IGES Global token caused 69 failures on unchanged Astra source; repairing that and 21 invalid positive graphs changes 170/260 to 261/261, including one new focused case. Astra MARC21 changes 2883/2900 to 2900/2900. BibTeX crossref threshold checks are now focused instead of remeasuring the same prerequisite across eight style tests. Failed-case counts are not counts of independent implementation defects. WordCount remains easy for these models; uniform success alone does not prove a broken evaluator.

Independent subagents reviewed source/spec alignment and candidate changes, including counterexamples and explicit permissions. Final ICal/BibTeX tests match reviewed candidates byte-for-byte; IGES differs only by three import-format blank-line edits with identical ASTs. Official Docker regrades reproduce the independently reviewed test outcomes. Reference and mutation-control results, limitations and source anchors appear in the linked records. The full applicable harness suite passed 359 tests plus 6 subtests; three host-Cargo cases were skipped and 23 Docker/model cases were deselected. The grader-image patch also passed a live offline image-identity probe and 119 independently rerun targeted checks. Strict Pyright and Ruff passed for the edited code. Rejected-tool evidence failures now leave authoritative token usage intact, and separate replacement guards verify prior audit contents as well as file hashes.

## Coverage: 50 of 112 missing cells recorded

The inventory already contained three runs per task/language for GPT-5.5, GPT-5.4, GPT-5.4-mini, GPT-5.3-Codex and GPT-5.2 at their configured top efforts. Astra, Sol, Terra and Luna had no published coverage on these tasks. This collection targets one Max run per missing cell; it does not imply three-repeat coverage, other reasoning efforts, or every possible GPT model. Earlier non-RS274 source artifacts were unavailable locally, so historical rows were not silently rescored.

| Task/language | Astra Max | Sol Max | Terra Max | Luna Max |
|---|---:|---:|---:|---:|
|bibtex-cpp|379/386|Pending|Pending|Pending|
|bibtex-js|382/386|Pending|Pending|Pending|
|bibtex-py|380/386|381/386|374/386|Retry: quota|
|bibtex-rs|383/386|Pending|Pending|Pending|
|gedcom-cpp|212/212|Pending|Pending|Pending|
|gedcom-js|212/212|Pending|Pending|Pending|
|gedcom-py|212/212|205/212|205/212|201/212|
|gedcom-rs|212/212|Pending|Pending|Pending|
|ical-cpp|466/468|Pending|Pending|Pending|
|ical-js|467/468|Pending|Pending|Pending|
|ical-py|468/468|Retry: quota|448/468|Retry: quota|
|ical-rs|465/468|Pending|Pending|Pending|
|iges-cpp|Pending|Pending|Pending|Pending|
|iges-js|Pending|Pending|Pending|Pending|
|iges-py|261/261|Retry: quota|Retry: quota|Pending|
|iges-rs|Pending|Pending|Pending|Pending|
|las-cpp|223/223|219/223|218/223|215/223|
|las-js|223/223|Pending|Pending|Pending|
|las-py|223/223|219/223|223/223|216/223|
|las-rs|223/223|Pending|Pending|Pending|
|marc21-cpp|2900/2900|Pending|Pending|Pending|
|marc21-js|2900/2900|Pending|Pending|Pending|
|marc21-py|2900/2900|Pending|2841/2900|Pending|
|marc21-rs|2900/2900|Pending|Pending|Pending|
|wordcount-cpp|46/46|46/46|46/46|46/46|
|wordcount-js|46/46|46/46|46/46|46/46|
|wordcount-py|46/46|46/46|46/46|46/46|
|wordcount-rs|46/46|46/46|46/46|46/46|

62 cells still need a qualifying result, including active runs. The earlier weekly limit interrupted five generations; their raw grader percentages are excluded. One Astra BibTeX attempt used hosted GitHub tools and is quarantined. Its raw data remains preserved. Capacity subsequently became available again and collection resumed. The previous four-worker queue is disabled. Resumed collection processes one submission at a time, including review before the next generation. Every excluded retry gets a fresh generation and preserves its previous artifacts and ledger.

## Conditions and accounting

The initial 35 valid completed runs predate explicit hosted-app disablement. Their complete session audit found no external tool invocation, and they are labeled `api-proxy-apps-available-unused`; this is distinct from future `api-only-apps-disabled` runs. Hosted app traffic can pass through the API and bypass the Docker socket proxy. The adapter now disables apps as well as web search, with three live isolation probes and independent review. Actual launch conditions remain recorded; generation metadata is not rewritten.

The v2 tool-call definition is unchanged. Session evidence exposed 19 rejected nested attempts across 17 of the initial 35 eligible completed generations that canonical items omitted. In that initial group, 12 exact totals were corrected; six totals are unavailable because other failed-wrapper evidence cannot establish an exact count (one such run had no explicit process rejection). Seventeen totals remain unchanged. Original token totals, reasoning, costs and generation-completion flags are preserved. Separate audits preserve complete prior publication bytes and existing regrade audit hash chains. The same omission was observed in one of 12 local historical RS274 attempts; its prior publication has not been silently rewritten. Subsequent generations use the corrected parser and are independently checked against their preserved sessions.

Estimated API-equivalent generation cost for the 50 qualifying completed runs: **$200.752997**. Excluded attempted generations total **$54.228829** at the recorded estimates, including partial quota runs. These are estimates, not the subscription bill. Reasoning tokens are a subset of output tokens and are not charged or added twice. Active runs are not included in these completed/excluded sums.

Agent image: `sha256:af2c19c8f457977011653519905408e861235272007daca50b92fc685f1aef73` (Codex CLI 0.153.4). Grader/reference image: `sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`. Saved-source regrades require no new inference or model cost. Normal grading now resolves, pins and records the actual grader image separately from the agent image; failed resolution preserves the completed generation and usage without inventing a score. Historical grader identity remains unknown unless explicitly recorded or supplied by a preserved regrade. The dashboard no longer substitutes an agent image for missing grader evidence.

Both dashboards now default to the newest exact scoring version available in their dataset, retain explicit older selections, and label mixed-version selections. The main dashboard retains its three-repeat automatic-selection policy; inspect this one-run collection by manually selecting available model combinations. The dashboard also preserves 19 richer historical stop summaries recovered from the tracked baseline, instead of relabeling context-limit endings as finished when original transcripts are missing. Archive entries are tied to exact generation identities and matching local events retain precedence. All 1776 baseline rows preserve every non-provenance field after rebuild. See [dashboard stop archive](../../operations/Dashboard-Stop-Archive.md).

Identified public choices and prose cleanup are listed separately in [public clarifications](public-clarifications.md). These 29 items are proposals for a later model-input revision, not new requirements applied to saved submissions.

Machine-readable records: [completed results](completed-results.json), [remaining coverage](remaining-coverage.json), [excluded attempts](excluded-attempts.json), [unchanged public inputs](public-inputs.json), and [baseline inventory](coverage-inventory.json). Raw transcripts, sessions, sources, original reports and complete local regrade directories remain on this workstation.

## Dispatch status

New dispatch is paused: One submission at a time: MARC21 Rust Astra Max is selected. Let it exit and finish review before dispatching another. Do not restart the parallel queue.
Active generations are allowed to finish and remain subject to full review.
