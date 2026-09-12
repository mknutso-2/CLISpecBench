# Non-RS274 scoring audit and GPT coverage

Checkpoint: 2026-09-12T13:55:27.090552+00:00. Local implementation revision `9bcfda5d877bc86b7ba91ebeb0dffc3e4e536be7`. Results are in the local publication tree; no push has been made for this task.

All seven other tasks contained scoring weaknesses: invalid fixtures, unsupported hidden restrictions, missing focused coverage, or failure amplification. Fixes keep every assembled model input unchanged across all28 task/language combinations. Patch versions, dated changelogs, public-spec comments and per-task validation records accompany the changes. Public prose ambiguities that cannot be resolved under its existing precedence or explicit permissions are deferred to a separate public-input revision.

| Task | Final version | Principal repair | Validation record |
|---|---|---|---|
| WordCount |1.0.4| Byte/line/delimiter boundaries, frequency ranking, JSON and CLI coverage; C++ reference fixes.|[WordCount](../WordCount-1.0.4.md)|
| LAS |2.0.3| Do not reward internal errors; valid waveform offsets, permitted representations and an explicit short ExtraBytes tail.|[LAS](../LAS-2.0.3.md)|
| GEDCOM |4.0.2| Optional cross-reference IDs, reciprocal family contexts and focused backlink negatives.|[GEDCOM](../GEDCOM-4.0.2.md)|
| MARC21 |3.0.2| Remove universal skip gates; repair fixed fields, currency/linkage examples and valid ordering contexts; leave ambiguous minima unscored.|[MARC21](../MARC21-3.0.2.md)|
| BibTeX |1.2.3| Valid BST prerequisites/stack fixtures, independent oracle goldens, mounted style fixtures and explicit approximation allowances.|[BibTeX](../BibTeX-1.2.3.md)|
| iCalendar |3.0.2| Defined recurrence sets, valid timezone/component/method fixtures and permitted representations.|[ICal](../ICal-3.0.2.md)|
| IGES |1.0.17| Legal shared Global data and typed reference graphs; independent Hollerith validation and focused semantic controls.|[IGES](../IGES-1.0.17.md)|

Failure amplification was material. One illegal shared IGES Global token caused69 failures on unchanged Astra source; repairing that and21 invalid positive graphs changes170/260 to261/261, including one new focused case. Astra MARC21 changes2883/2900 to2900/2900. BibTeX crossref threshold checks are now focused instead of remeasuring the same prerequisite across eight style tests. Failed-case counts are not counts of independent implementation defects. WordCount remains easy for these models; uniform success alone does not prove a broken evaluator.

Independent subagents reviewed source/spec alignment and candidate changes, including counterexamples and explicit permissions. Final ICal/BibTeX tests match reviewed candidates byte-for-byte; IGES differs only by three import-format blank-line edits with identical ASTs. The final five Docker regrades reproduced the independently reviewed counts exactly. Reference and mutation-control results, limitations and source anchors appear in the linked records. The final harness/accounting checks passed103 tests plus6 subtests, and52 publication/regrade tests passed; strict Pyright and Ruff checks passed for the edited code. Further telemetry hardening is under independent review.

## Coverage: 35 of112 missing cells recorded

The inventory already contained three runs per task/language for GPT-5.5, GPT-5.4, GPT-5.4-mini, GPT-5.3-Codex and GPT-5.2 at their configured top efforts. Astra, Sol, Terra and Luna had no published coverage on these tasks. This collection targets one Max run per missing cell; it does not imply three-repeat coverage, other reasoning efforts, or every possible GPT model. Earlier non-RS274 source artifacts were unavailable locally, so historical rows were not silently rescored.

| Task/language | Astra Max | Sol Max | Terra Max | Luna Max |
|---|---:|---:|---:|---:|
|bibtex-cpp|Pending|Pending|Pending|Pending|
|bibtex-js|Pending|Pending|Pending|Pending|
|bibtex-py|Retry: excluded|382/386|375/386|Retry: quota|
|bibtex-rs|Pending|Pending|Pending|Pending|
|gedcom-cpp|Running|Pending|Pending|Pending|
|gedcom-js|Running|Pending|Pending|Pending|
|gedcom-py|212/212|205/212|205/212|201/212|
|gedcom-rs|Pending|Pending|Pending|Pending|
|ical-cpp|Pending|Pending|Pending|Pending|
|ical-js|Pending|Pending|Pending|Pending|
|ical-py|468/468|Retry: quota|448/468|Retry: quota|
|ical-rs|Pending|Pending|Pending|Pending|
|iges-cpp|Pending|Pending|Pending|Pending|
|iges-js|Pending|Pending|Pending|Pending|
|iges-py|261/261|Retry: quota|Retry: quota|Pending|
|iges-rs|Pending|Pending|Pending|Pending|
|las-cpp|223/223|219/223|218/223|215/223|
|las-js|Running|Pending|Pending|Pending|
|las-py|223/223|219/223|223/223|216/223|
|las-rs|Running|Pending|Pending|Pending|
|marc21-cpp|Pending|Pending|Pending|Pending|
|marc21-js|Pending|Pending|Pending|Pending|
|marc21-py|2900/2900|Pending|2841/2900|Pending|
|marc21-rs|Pending|Pending|Pending|Pending|
|wordcount-cpp|46/46|46/46|46/46|46/46|
|wordcount-js|46/46|46/46|46/46|46/46|
|wordcount-py|46/46|46/46|46/46|46/46|
|wordcount-rs|46/46|46/46|46/46|46/46|

77 cells still need a qualifying result, including active runs. The earlier weekly limit interrupted five generations; their raw grader percentages are excluded. One Astra BibTeX attempt used hosted GitHub tools and is quarantined. Its raw data remains preserved. The account limit subsequently reset and collection resumed; the earlier reset-time estimate is no longer the current blocker.

## Conditions and accounting

The initial35 valid completed runs predate explicit hosted-app disablement. Their complete session audit found no external tool invocation, and they are labeled `api-proxy-apps-available-unused`; this is distinct from future `api-only-apps-disabled` runs. Hosted app traffic can pass through the API and bypass the Docker socket proxy. The adapter now disables apps as well as web search, with three live isolation probes and independent review. Actual launch conditions remain recorded; generation metadata is not rewritten.

The v2 tool-call definition is unchanged. Session evidence exposed19 rejected nested attempts across17 completed generations that canonical items omitted. Of35 eligible completed runs,12 exact totals were corrected; six totals are unavailable because other failed-wrapper evidence cannot establish an exact count (one such run had no explicit process rejection). Seventeen totals remain unchanged. Original token totals, reasoning, costs and generation-completion flags are preserved. Separate audits preserve complete prior publication bytes and existing regrade audit hash chains. The same omission was observed in one of12 local historical RS274 attempts; its prior publication has not been silently rewritten.

Estimated API-equivalent generation cost for the 35 qualifying completed runs: **$101.897649**. Excluded attempted generations total **$54.228829** at the recorded estimates, including partial quota runs. These are estimates, not the subscription bill. Reasoning tokens are a subset of output tokens and are not charged or added twice. Active runs are not included in these completed/excluded sums.

Agent image: `sha256:af2c19c8f457977011653519905408e861235272007daca50b92fc685f1aef73` (Codex CLI0.153.4). Grader/reference image: `sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`. Saved-source regrades require no new inference or model cost.

Machine-readable records: [completed results](completed-results.json), [remaining coverage](remaining-coverage.json), [excluded attempts](excluded-attempts.json), [unchanged public inputs](public-inputs.json), and [baseline inventory](coverage-inventory.json). Raw transcripts, sessions, sources, original reports and complete local regrade directories remain on this workstation.
