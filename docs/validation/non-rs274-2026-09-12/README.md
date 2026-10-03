# Non-RS274 scoring audit and GPT coverage

**October 2 Windows update:** [Current handoff and ownership](../../operations/Non-RS274-Cross-Computer-Handoff.md). All 39 authorized Windows generation cells are reviewed and published in the canonical results tree. The checkpoint is 111/112; only the already-completed Sol IGES Python run awaits transferred artifacts. No evaluation worker remains active, and the same-chat collection heartbeat is paused. The user directed us to document the [ICal raw-projection issue for a future fix](ical-valarm-publication-hold.md) and continue with frozen scores and explicit caveats; the [IGES fixture/contract follow-up](iges-frozen-suite-followup.md) follows the same policy. This checkpoint includes the publications, portable reviews and main dashboard index; raw artifacts remain on the Windows workstation. This supersedes earlier dispatch and pause notes.

Current machine-readable checkpoint timestamps are in `completed-results.json` and
`remaining-coverage.json`. The Windows generations use revision `8807848`.
Historical source-machine checkpoint: 2026-10-01T11:39:00.784285+00:00,
revision `7e057755691e8bce24aef32b4f66adcd2487b8c2`.

The user resumed work on September 30 with one submission at a time: finish each retained review before new generation, then finish and review each new run before starting another. The previous parallel queue remains disabled. See the [resume instructions](../../operations/Non-RS274-Audit-Resume.md).

All seven other tasks contained scoring weaknesses: invalid fixtures, unsupported hidden restrictions, missing focused coverage, or failure amplification. Fixes keep every assembled model input unchanged across all 28 task/language combinations. Patch versions, dated changelogs, public-spec comments and per-task validation records accompany the changes. Public prose ambiguities that cannot be resolved under its existing precedence or explicit permissions are deferred to a separate public-input revision.

| Task | Final version | Principal repair | Validation record |
|---|---|---|---|
| WordCount |1.0.4| Byte/line/delimiter boundaries, frequency ranking, JSON and CLI coverage; C++ reference fixes.|[WordCount](../WordCount-1.0.4.md)|
| LAS |2.0.5| Do not reward internal errors; valid waveform offsets/representations and independent storage/ExtraBytes negatives; zero-point-waveform fixtures retain required file-level metadata.|[LAS](../LAS-2.0.5.md)|
| GEDCOM |4.0.3| Optional cross-reference IDs, reciprocal family contexts, focused backlink negatives and an isolated void-pointer case.|[GEDCOM](../GEDCOM-4.0.3.md)|
| MARC21 |3.0.2| Remove universal skip gates; repair fixed fields, currency/linkage examples and valid ordering contexts; leave ambiguous minima unscored.|[MARC21](../MARC21-3.0.2.md)|
| BibTeX |1.2.5| Valid BST/stack fixtures, independent oracle goldens, permitted approximations, corrected past-end names and EOF behavior, and isolated semantic output probes.|[BibTeX](../BibTeX-1.2.5.md)|
| iCalendar |3.0.5| Valid recurrence/timezone/method/calendar fixtures; unsupported alarm recovery oracle removed; orphan diagnostics accepted in either phase and ADD metadata ambiguity left unscored.|[ICal](../ICal-3.0.5.md)|
| IGES |1.0.21| Legal Global/typed/Logical/View fixtures; normalized appendix metadata/Real literals and three integration cases in place of fifteen repeated prerequisites.|[IGES](../IGES-1.0.21.md)|

Failure amplification was material. One illegal shared IGES Global token caused 69 failures on unchanged Astra source; repairing that and 21 invalid positive graphs changed 170/260 to 261/261 under 1.0.17, including one new focused case. IGES 1.0.19 then corrects appendix metadata and changes 15 integration cases to 3 (261-to-249 total), retaining their observations while reducing repeated penalties. Astra Rust changes 245/261 to 247/249 with two real defects remaining; score movement reflects fixture and weighting corrections, not source improvements. Astra MARC21 changes 2883/2900 to 2900/2900. BibTeX crossref threshold checks are now focused instead of remeasuring the same prerequisite across eight style tests. Failed-case counts are not counts of independent implementation defects. WordCount remains easy for these models; uniform success alone does not prove a broken evaluator.

Independent subagents reviewed source/spec alignment and candidate changes, including counterexamples and explicit permissions. The September 12 ICal/BibTeX tests matched their reviewed candidates byte-for-byte. The subsequent BibTeX 1.2.5 EOF correction has independent source/oracle review, a 386/386 reference pass, and an EOF-flush mutation failing only its dedicated case; all eight retained-source official regrades were processed sequentially. The original IGES 1.0.17 candidate differed only by three import-format blank-line edits with identical ASTs; the separately reviewed 1.0.18 repair replaces a remaining invalid Face writer fixture with a legal context and focused boolean observation. The independently reviewed 1.0.19 patch normalizes conflicted appendix fields and consolidates repeated integration prerequisites, with three full reference passes and four deliberate mutation controls. Official Docker regrades reproduce the independently reviewed test outcomes. Reference and mutation-control results, limitations and source anchors appear in the linked records. The full applicable harness suite passed 359 tests plus 6 subtests; three host-Cargo cases were skipped and 23 Docker/model cases were deselected. The grader-image patch also passed a live offline image-identity probe and 119 independently rerun targeted checks. Strict Pyright and Ruff passed for the edited code. Rejected-tool evidence failures now leave authoritative token usage intact, and separate replacement guards verify prior audit contents as well as file hashes.

## Coverage: 111 of 112 missing cells recorded

The inventory already contained three runs per task/language for GPT-5.5, GPT-5.4, GPT-5.4-mini, GPT-5.3-Codex and GPT-5.2 at their configured top efforts. Astra, Sol, Terra and Luna had no published coverage on these tasks. This collection targets one Max run per missing cell; it does not imply three-repeat coverage, other reasoning efforts, or every possible GPT model. Earlier non-RS274 source artifacts were unavailable locally, so historical rows were not silently rescored.

| Task/language | Astra Max | Sol Max | Terra Max | Luna Max |
|---|---:|---:|---:|---:|
|bibtex-cpp|378/386|378/386|362/386|368/386|
|bibtex-js|381/386|383/386|372/386|370/386|
|bibtex-py|379/386|380/386|373/386|355/386|
|bibtex-rs|382/386|379/386|382/386|365/386|
|gedcom-cpp|212/212|212/212|169/212|164/212 (VOID mapping caveat)|
|gedcom-js|212/212|205/212|118/212|202/212|
|gedcom-py|212/212|205/212|205/212|201/212|
|gedcom-rs|212/212|212/212|128/212|165/212 (shared-fixture caveat)|
|ical-cpp|466/467|464/467|456/467 (raw-projection caveat)|450/467|
|ical-js|466/467|462/467|447/467 (raw-projection caveat)|457/467|
|ical-py|467/467|466/467|448/467|456/467|
|ical-rs|465/467|461/467|454/467 (raw-projection caveat)|442/467 (projection/fixture caveats)|
|iges-cpp|247/249|245/249|244/249|231/249 (mapping/writer-test caveats)|
|iges-js|248/249|246/249|228/249 (fixture/contract caveats)|243/249|
|iges-py|249/249|Review: 244/249 provisional|247/249|245/249|
|iges-rs|247/249|244/249|248/249|239/249 (mapping/writer-test caveats)|
|las-cpp|223/223|223/223|222/223|219/223|
|las-js|223/223|223/223|223/223|219/223|
|las-py|223/223|223/223|223/223|220/223|
|las-rs|223/223|223/223|223/223|219/223|
|marc21-cpp|2900/2900|2876/2900|2876/2900|2877/2900|
|marc21-js|2900/2900|2848/2900|2848/2900|2838/2900|
|marc21-py|2900/2900|2896/2900|2841/2900|2884/2900|
|marc21-rs|2900/2900|2900/2900|2857/2900|2887/2900|
|wordcount-cpp|46/46|46/46|46/46|46/46|
|wordcount-js|46/46|46/46|46/46|46/46|
|wordcount-py|46/46|46/46|46/46|46/46|
|wordcount-rs|46/46|46/46|46/46|46/46|

1 cell still needs a qualifying publication: completed Sol IGES Python awaiting artifact transfer/review. All 39 authorized Windows generations are completed, reviewed and locally published; do not regenerate the transfer-only run. The earlier weekly limit interrupted five generations; their raw grader percentages are excluded. One Astra BibTeX attempt used hosted GitHub tools and is quarantined. Its raw data remains preserved. The old source-machine queue stays disabled. The Windows continuation used at most four concurrent slots, each held through substantive review. Excluded retries preserved their previous artifacts and ledgers.

Provider-capacity interruptions are tracked separately from account-quota interruptions. They are excluded from correctness scores, preserve partial usage, and require fresh attempts; see the excluded-attempt records for each cause.

## Conditions and accounting

The initial 35 valid completed runs predate explicit hosted-app disablement. Their complete session audit found no external tool invocation, and they are labeled `api-proxy-apps-available-unused`; this is distinct from future `api-only-apps-disabled` runs. Hosted app traffic can pass through the API and bypass the Docker socket proxy. The adapter now disables apps as well as web search, with three live isolation probes and independent review. Actual launch conditions remain recorded; generation metadata is not rewritten.

The v2 tool-call definition is unchanged. Session evidence exposed 19 rejected nested attempts across 17 of the initial 35 eligible completed generations that canonical items omitted. In that initial group, 12 exact totals were corrected; six totals are unavailable because other failed-wrapper evidence cannot establish an exact count (one such run had no explicit process rejection). Seventeen totals remain unchanged. Original token totals, reasoning, costs and generation-completion flags are preserved. Separate audits preserve complete prior publication bytes and existing regrade audit hash chains. The same omission was observed in one of 12 local historical RS274 attempts; its prior publication has not been silently rewritten. Subsequent generations use the corrected parser and are independently checked against their preserved sessions.

Estimated API-equivalent generation cost for the 111 qualifying completed runs: **$604.420091**. Excluded attempted generations total **$54.862522** at the recorded estimates, including partial quota runs. These are estimates, not the subscription bill. Reasoning tokens are a subset of output tokens and are not charged or added twice. Unreviewed runs are not included. Terra IGES C++/Python, Luna BibTeX C++/JS/Rust, Luna ICal C++/Python/Rust and Luna IGES Python secondary cumulative telemetry each include a compaction request omitted by the existing canonical accounting basis; Luna ICal JavaScript and IGES Rust each include three, Luna IGES JavaScript four and Luna IGES C++ five. Their reviews document this limitation without changing the collection's counter policy.

Agent image: `sha256:af2c19c8f457977011653519905408e861235272007daca50b92fc685f1aef73` (Codex CLI 0.153.4). Grader/reference image: `sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`. Saved-source regrades require no new inference or model cost. Normal grading now resolves, pins and records the actual grader image separately from the agent image; failed resolution preserves the completed generation and usage without inventing a score. Historical grader identity remains unknown unless explicitly recorded or supplied by a preserved regrade. The dashboard no longer substitutes an agent image for missing grader evidence.

Both dashboards now default to the newest exact scoring version available in their dataset, retain explicit older selections, and label mixed-version selections. The main dashboard retains its three-repeat automatic-selection policy; inspect this one-run collection by manually selecting available model combinations. The dashboard also preserves 19 richer historical stop summaries recovered from the tracked baseline, instead of relabeling context-limit endings as finished when original transcripts are missing. Archive entries are tied to exact generation identities and matching local events retain precedence. All 1776 baseline rows preserve every non-provenance field after rebuild. See [dashboard stop archive](../../operations/Dashboard-Stop-Archive.md).

LAS 2.0.5 withdraws the earlier interpretation that four descriptor/storage-free zero-waveform positives measured model defects. The repaired fixtures retain valid file-level metadata and isolate the point-level zero waveform. All 16 retained sources preserve the other 219 outcomes; nine gain four passes and seven remain unchanged. The new Luna Rust result scores 219/223, with four observations of one superseded-record defect remaining. Separate regrades preserve complete historical publications and original generation bytes. See [the measured migration](../LAS-2.0.5.md). A session-backed audit also recovers Luna C++ tool calls from unavailable to 91 (88 canonical actions plus three rejected requests); non-tool usage and costs remain unchanged.

Identified public choices and prose cleanup are listed separately in [public clarifications](public-clarifications.md). These items are proposals for a later model-input revision, not new requirements applied to saved submissions.

ICal 3.0.4 follows the cancellation/alarm correction with valid component-bearing calendar fixtures and phase/metadata-neutral diagnostic checks. Seven retained sources were regraded sequentially with all 460 unaffected outcomes preserved; the reference passes 467/467. A combined permitted-policy control changes from 0/7 to 7/7, while four negative controls retain the exact intended failures. Original raw scores and complete prior publications remain in audit history. See [ICal validation](../ICal-3.0.4.md).

ICal 3.0.5 isolates CANCEL fixtures with an incremented sequence and exact STATUS/SEQUENCE warning metadata. Nine saved sources were regraded sequentially with all 461 unaffected outcomes preserved. The eight prior scores are unchanged; the new Sol Python retry improves from 463/467 to 466/467, leaving one genuine ADD diagnostic defect. The reference passes 467/467, and three negative controls each fail only their named check. The raw null tool metric is preserved while session evidence supports 230 calls under the existing v2 definition. See [ICal 3.0.5 validation](../ICal-3.0.5.md).

Machine-readable records: [completed results](completed-results.json), [remaining coverage](remaining-coverage.json), [excluded attempts](excluded-attempts.json), [unchanged public inputs](public-inputs.json), and [baseline inventory](coverage-inventory.json). Raw transcripts, sessions, sources, original reports and complete local regrade directories remain on this workstation.

## Dispatch status

Windows owns the authorized four-slot continuation. The ICal ambiguity is
documented for a future fix; all three newly reviewed ICal scores remain frozen
with caveats. The four Sol MARC21 and sixteen new Terra results are reviewed;
Terra now has all 28 target cells. At October 2 14:05 Chicago, Luna BibTeX
cpp/js/py/rs are reviewed/published at368/386,370/386,355/386 and365/386;
GEDCOM cpp at164/212. All Luna GEDCOM languages are now reviewed/published.
At October 2 15:45 Chicago, Luna ICal C++ is reviewed/published at450/467;
its17 observations map to seven defect groups, not the known raw-projection issue.
Python is reviewed/published at456/467 and Rust at442/467. Rust retains explicit
[projection and fixture caveats](ical-valarm-publication-hold.md#luna-rust-follow-up--october-2),
including an RFC-invalid floating UNTIL in a timezone positive fixture.
At October 2 16:12 Chicago, ICal JavaScript is reviewed/published at457/467.
Its ten failures are implementation defects, not the known projection caveats.
Raw432 tools and canonical$1.912947 reconcile; three compactions and a
post-completion cleanup logging anomaly are explicitly documented in its audit.
At October 2 16:25 Chicago, Luna IGES JavaScript is reviewed/published at243/249.
Six observations map to four defects: extra query wrapper3, illegal0H1,
omitted trailing DDF1 and input final-newline overrestriction1. Raw313tools and
canonical$1.524918 reconcile; four compactions are separately documented.
At October 2 17:14 Chicago, IGES Python245/249 and MARC21 C++2877/2900
are independently reviewed/published. Python's four failures map to EOF-newline
overvalidation, Type114 row-boundary ordering and Type416 form2 filename loss;
one compaction is documented, with229tools recovered only in publication.
MARC21's23 failures map to missing008 positional checks, omitted006k and018$a.
Its104tools and canonical cost reconcile without correction or compaction.
At October 2 17:22 Chicago, IGES C++231/249 is independently reviewed/published.
Thirteen observations have concrete codec/default/type causes; two AVDT mapping
and three first-P-line assertion caveats are documented in the future-fix note.
Raw377tools/$1.599920 reconcile; five compactions are separately documented.
At October 2 17:54 Chicago, IGES Rust239/249 and MARC21 JavaScript2838/2900
and Python2884/2900 are independently reviewed/published. Rust has five concrete
defect observations plus five known mapping/writer-test caveats. Its attempted
GitHub source fetch returned only a proxy403; no source was retrieved. Exact307
tools are recovered publication-only, with three compactions disclosed. MARC21
failures arise from missing008 checks and lossy public-HTML rule extraction;
JS99tools are recovered publication-only, Python raw61 remains unchanged.
At October 2 18:18 Chicago, Luna MARC21 Rust2887/2900 is independently
reviewed/published. Its13 failures map to007 optional-length restrictions4,
forbidden category fill1, omitted008 code checks4, and missing018$a4.
Exact82tools are recovered publication-only; canonical$0.439627 reconciles
without compaction. All39 Windows cells are finalized, with no active workers.
The same-chat heartbeat is paused. Sol IGES Python is still transfer-only.
The local offline IGES
reference passed 249/249. Check the local
`automation_logs/non-rs274-oct1/` launch/review ledgers and actual Docker state;
do not infer active workers from this document or restart the old source queue.
The local images differ from the original collection's images, as documented in
the current handoff. Raw results remain unchanged; exact tool-count recovery is
recorded in per-UID audits under `regraded_results/tool-counts/2026-10-01/`.
The sixteen new Terra reviews and accounting audits are under `reviews/`
here. BibTeX JavaScript's attempted package acquisition was blocked; no successful
external reference retrieval was evidenced. GEDCOM's 107 tool total excludes two
whole-script JavaScript syntax failures that invoked no underlying tool.
BibTeX Rust's attempted CTAN connection was also blocked. Its exact 324-tool total
is recovered from 320 canonical actions plus four rejected patches; six no-op
wrappers are excluded. The raw null remains untouched, and the portable review
includes independent accounting evidence. Both dashboards retain all previous
rows; the current checkpoint export contains 1,215,735 outcomes across 1887 completed runs.
GEDCOM Rust's 128-tool total includes four pre-item rejections and excludes one
whole-module SyntaxError that executed no tool. Its 84 semantic failures are
documented independently; no infrastructure rerun or score adjustment is indicated.

Terra MARC21 JS/Rust completed at 2848/2900 and 2857/2900. JS omits eight
documented field definitions and fixed-field semantics; Rust lacks fixed-field
semantics and rejects valid 018$a after lossy rule extraction. Independent reviews
found no new oracle ambiguity. Their raw null tool counts remain preserved;
session-backed publication corrections establish 83 and 73 underlying calls.

Luna BibTeX C++/JS have independent correctness and accounting reviews, with
exact session-backed tool counts309/218. Their remaining failures are supported
by authoritative WEB, while several behaviors follow misleading summary prose;
the already documented [future summary cleanup](public-clarifications.md#bibtex-125)
remains deferred. Each has one identified compaction request excluded by the
existing canonical accounting policy. No successful external retrieval occurred.

Luna BibTeX Python's31 failed observations include ten internal-error exits from
one name-scanner bounds bug, reproduced in an isolated offline grader container.
Six more reflect suppression of user warning messages; the missing public JSON
kind mapping deserves future clarification, without inventing a scored category.
Other failures are compatibility differences documented in its independent review.
Exact148tools are recovered; raw nulls, tokens and$0.524032 cost remain unchanged.
A single proxy connection reset recovered eleven minutes before normal completion;
its complete traceback is preserved and narrowly hash-gated, not silently dropped.
Structured relay-disconnect logging is a future harness follow-up, not changed here.

Luna BibTeX Rust's21 failed observations include three manifestations of one
negative-substring defect (including both alpha-style parity cases). Its raw213
tools and$0.868687 cost are exact; one compaction is separately reconciled.
Luna GEDCOM C++'s48 failures include16 shared BIRT Y rejections, not independent
date/schema/ZIP defects. Three concern the under-specified VOID JSON projection,
documented in [future clarifications](public-clarifications.md#gedcom-403);
the source supports VOID semantically using JSON null. Other failures cover
context-sensitive grammar, optional xrefs, time/age, backlinks and archive checks.
Raw149tools and$0.691752 cost are exact, no compaction. Both independent reviews
and separate accounting reviews are preserved in portable per-UID audits; no
successful external retrieval or environment-caused interruption was found.
