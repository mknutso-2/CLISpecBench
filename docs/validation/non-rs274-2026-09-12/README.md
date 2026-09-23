# Non-RS274 scoring audit and GPT coverage

Checkpoint: 2026-09-23T01:18:51.227849+00:00. Local implementation revision `3330986bca154c387d60b51022fe173bfe3554da`. Results are in the local publication tree; no push has been made for this task.

Collection is paused at the user’s request. Only the existing IGES C++ / Sol Max run may finish; do not launch more models until the user asks to resume. See the [resume instructions](../../operations/Non-RS274-Audit-Resume.md).

All seven other tasks contained scoring weaknesses: invalid fixtures, unsupported hidden restrictions, missing focused coverage, or failure amplification. Fixes keep every assembled model input unchanged across all 28 task/language combinations. Patch versions, dated changelogs, public-spec comments and per-task validation records accompany the changes. Public prose ambiguities that cannot be resolved under its existing precedence or explicit permissions are deferred to a separate public-input revision.

| Task | Final version | Principal repair | Validation record |
|---|---|---|---|
| WordCount |1.0.4| Byte/line/delimiter boundaries, frequency ranking, JSON and CLI coverage; C++ reference fixes.|[WordCount](../WordCount-1.0.4.md)|
| LAS |2.0.5| Do not reward internal errors; valid waveform offsets/representations and independent storage/ExtraBytes negatives; zero-point-waveform fixtures retain required file-level metadata.|[LAS](../LAS-2.0.5.md)|
| GEDCOM |4.0.3| Optional cross-reference IDs, reciprocal family contexts, focused backlink negatives and an isolated void-pointer case.|[GEDCOM](../GEDCOM-4.0.3.md)|
| MARC21 |3.0.2| Remove universal skip gates; repair fixed fields, currency/linkage examples and valid ordering contexts; leave ambiguous minima unscored.|[MARC21](../MARC21-3.0.2.md)|
| BibTeX |1.2.5| Valid BST/stack fixtures, independent oracle goldens, permitted approximations, corrected past-end names and EOF behavior, and isolated semantic output probes.|[BibTeX](../BibTeX-1.2.5.md)|
| iCalendar |3.0.4| Valid recurrence/timezone/method/calendar fixtures; unsupported alarm recovery oracle removed; orphan diagnostics accepted in either phase and ADD metadata ambiguity left unscored.|[ICal](../ICal-3.0.4.md)|
| IGES |1.0.19| Legal Global/typed/Logical fixtures; normalized appendix metadata and three integration cases in place of fifteen repeated prerequisites.|[IGES](../IGES-1.0.19.md)|

Failure amplification was material. One illegal shared IGES Global token caused 69 failures on unchanged Astra source; repairing that and 21 invalid positive graphs changed 170/260 to 261/261 under 1.0.17, including one new focused case. IGES 1.0.19 then corrects appendix metadata and changes 15 integration cases to 3 (261-to-249 total), retaining their observations while reducing repeated penalties. Astra Rust changes 245/261 to 247/249 with two real defects remaining; score movement reflects fixture and weighting corrections, not source improvements. Astra MARC21 changes 2883/2900 to 2900/2900. BibTeX crossref threshold checks are now focused instead of remeasuring the same prerequisite across eight style tests. Failed-case counts are not counts of independent implementation defects. WordCount remains easy for these models; uniform success alone does not prove a broken evaluator.

Independent subagents reviewed source/spec alignment and candidate changes, including counterexamples and explicit permissions. The September 12 ICal/BibTeX tests matched their reviewed candidates byte-for-byte. The subsequent BibTeX 1.2.5 EOF correction has independent source/oracle review, a 386/386 reference pass, and an EOF-flush mutation failing only its dedicated case; all eight retained-source official regrades were processed sequentially. The original IGES 1.0.17 candidate differed only by three import-format blank-line edits with identical ASTs; the separately reviewed 1.0.18 repair replaces a remaining invalid Face writer fixture with a legal context and focused boolean observation. The independently reviewed 1.0.19 patch normalizes conflicted appendix fields and consolidates repeated integration prerequisites, with three full reference passes and four deliberate mutation controls. Official Docker regrades reproduce the independently reviewed test outcomes. Reference and mutation-control results, limitations and source anchors appear in the linked records. The full applicable harness suite passed 359 tests plus 6 subtests; three host-Cargo cases were skipped and 23 Docker/model cases were deselected. The grader-image patch also passed a live offline image-identity probe and 119 independently rerun targeted checks. Strict Pyright and Ruff passed for the edited code. Rejected-tool evidence failures now leave authoritative token usage intact, and separate replacement guards verify prior audit contents as well as file hashes.

## Coverage: 69 of 112 missing cells recorded

The inventory already contained three runs per task/language for GPT-5.5, GPT-5.4, GPT-5.4-mini, GPT-5.3-Codex and GPT-5.2 at their configured top efforts. Astra, Sol, Terra and Luna had no published coverage on these tasks. This collection targets one Max run per missing cell; it does not imply three-repeat coverage, other reasoning efforts, or every possible GPT model. Earlier non-RS274 source artifacts were unavailable locally, so historical rows were not silently rescored.

| Task/language | Astra Max | Sol Max | Terra Max | Luna Max |
|---|---:|---:|---:|---:|
|bibtex-cpp|378/386|378/386|Pending|Pending|
|bibtex-js|381/386|383/386|Pending|Pending|
|bibtex-py|379/386|380/386|373/386|Retry: quota|
|bibtex-rs|382/386|379/386|Pending|Pending|
|gedcom-cpp|212/212|212/212|Pending|Pending|
|gedcom-js|212/212|205/212|Pending|Pending|
|gedcom-py|212/212|205/212|205/212|201/212|
|gedcom-rs|212/212|212/212|Pending|Pending|
|ical-cpp|466/467|464/467|Pending|Pending|
|ical-js|466/467|462/467|Pending|Pending|
|ical-py|467/467|466/467|448/467|Retry: quota|
|ical-rs|465/467|461/467|Pending|Pending|
|iges-cpp|247/249|Running|Pending|Pending|
|iges-js|248/249|Pending|Pending|Pending|
|iges-py|249/249|Retry: quota|Retry: quota|Pending|
|iges-rs|247/249|Pending|Pending|Pending|
|las-cpp|223/223|223/223|222/223|219/223|
|las-js|223/223|223/223|223/223|219/223|
|las-py|223/223|223/223|223/223|220/223|
|las-rs|223/223|223/223|223/223|219/223|
|marc21-cpp|2900/2900|Pending|Pending|Pending|
|marc21-js|2900/2900|Pending|Pending|Pending|
|marc21-py|2900/2900|Pending|2841/2900|Pending|
|marc21-rs|2900/2900|Pending|Pending|Pending|
|wordcount-cpp|46/46|46/46|46/46|46/46|
|wordcount-js|46/46|46/46|46/46|46/46|
|wordcount-py|46/46|46/46|46/46|46/46|
|wordcount-rs|46/46|46/46|46/46|46/46|

43 cells still need a qualifying result, including active runs. The earlier weekly limit interrupted five generations; their raw grader percentages are excluded. One Astra BibTeX attempt used hosted GitHub tools and is quarantined. Its raw data remains preserved. Capacity subsequently became available again and collection resumed. The previous four-worker queue remains disabled. Collection was proceeding one submission at a time before the current user-requested pause; independent review remains required before publication. Every excluded retry gets a fresh generation and preserves its previous artifacts and ledger.

Provider-capacity interruptions are tracked separately from account-quota interruptions. They are excluded from correctness scores, preserve partial usage, and require fresh attempts; see the excluded-attempt records for each cause.

## Conditions and accounting

The initial 35 valid completed runs predate explicit hosted-app disablement. Their complete session audit found no external tool invocation, and they are labeled `api-proxy-apps-available-unused`; this is distinct from future `api-only-apps-disabled` runs. Hosted app traffic can pass through the API and bypass the Docker socket proxy. The adapter now disables apps as well as web search, with three live isolation probes and independent review. Actual launch conditions remain recorded; generation metadata is not rewritten.

The v2 tool-call definition is unchanged. Session evidence exposed 19 rejected nested attempts across 17 of the initial 35 eligible completed generations that canonical items omitted. In that initial group, 12 exact totals were corrected; six totals are unavailable because other failed-wrapper evidence cannot establish an exact count (one such run had no explicit process rejection). Seventeen totals remain unchanged. Original token totals, reasoning, costs and generation-completion flags are preserved. Separate audits preserve complete prior publication bytes and existing regrade audit hash chains. The same omission was observed in one of 12 local historical RS274 attempts; its prior publication has not been silently rewritten. Subsequent generations use the corrected parser and are independently checked against their preserved sessions.

Estimated API-equivalent generation cost for the 69 qualifying completed runs: **$397.708987**. Excluded attempted generations total **$54.862522** at the recorded estimates, including partial quota runs. These are estimates, not the subscription bill. Reasoning tokens are a subset of output tokens and are not charged or added twice. Active runs are not included in these completed/excluded sums.

Agent image: `sha256:af2c19c8f457977011653519905408e861235272007daca50b92fc685f1aef73` (Codex CLI 0.153.4). Grader/reference image: `sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`. Saved-source regrades require no new inference or model cost. Normal grading now resolves, pins and records the actual grader image separately from the agent image; failed resolution preserves the completed generation and usage without inventing a score. Historical grader identity remains unknown unless explicitly recorded or supplied by a preserved regrade. The dashboard no longer substitutes an agent image for missing grader evidence.

Both dashboards now default to the newest exact scoring version available in their dataset, retain explicit older selections, and label mixed-version selections. The main dashboard retains its three-repeat automatic-selection policy; inspect this one-run collection by manually selecting available model combinations. The dashboard also preserves 19 richer historical stop summaries recovered from the tracked baseline, instead of relabeling context-limit endings as finished when original transcripts are missing. Archive entries are tied to exact generation identities and matching local events retain precedence. All 1776 baseline rows preserve every non-provenance field after rebuild. See [dashboard stop archive](../../operations/Dashboard-Stop-Archive.md).

LAS 2.0.5 withdraws the earlier interpretation that four descriptor/storage-free zero-waveform positives measured model defects. The repaired fixtures retain valid file-level metadata and isolate the point-level zero waveform. All 16 retained sources preserve the other 219 outcomes; nine gain four passes and seven remain unchanged. The new Luna Rust result scores 219/223, with four observations of one superseded-record defect remaining. Separate regrades preserve complete historical publications and original generation bytes. See [the measured migration](../LAS-2.0.5.md). A session-backed audit also recovers Luna C++ tool calls from unavailable to 91 (88 canonical actions plus three rejected requests); non-tool usage and costs remain unchanged.

Identified public choices and prose cleanup are listed separately in [public clarifications](public-clarifications.md). These items are proposals for a later model-input revision, not new requirements applied to saved submissions.

ICal 3.0.4 follows the cancellation/alarm correction with valid component-bearing calendar fixtures and phase/metadata-neutral diagnostic checks. Seven retained sources were regraded sequentially with all 460 unaffected outcomes preserved; the reference passes 467/467. A combined permitted-policy control changes from 0/7 to 7/7, while four negative controls retain the exact intended failures. Original raw scores and complete prior publications remain in audit history. See [ICal validation](../ICal-3.0.4.md).

ICal 3.0.5 isolates CANCEL fixtures with an incremented sequence and exact STATUS/SEQUENCE warning metadata. Nine saved sources were regraded sequentially with all 461 unaffected outcomes preserved. The eight prior scores are unchanged; the new Sol Python retry improves from 463/467 to 466/467, leaving one genuine ADD diagnostic defect. The reference passes 467/467, and three negative controls each fail only their named check. The raw null tool metric is preserved while session evidence supports 230 calls under the existing v2 definition. See [ICal 3.0.5 validation](../ICal-3.0.5.md).

Machine-readable records: [completed results](completed-results.json), [remaining coverage](remaining-coverage.json), [excluded attempts](excluded-attempts.json), [unchanged public inputs](public-inputs.json), and [baseline inventory](coverage-inventory.json). Raw transcripts, sessions, sources, original reports and complete local regrade directories remain on this workstation.

## Dispatch status

New dispatch is paused: User requested stopping future processing near the weekly usage allotment. Let only the already active IGES C++ / Sol Max submission finish; no further generation or queue restart until the user explicitly resumes.
Active generations are allowed to finish and remain subject to full review.
