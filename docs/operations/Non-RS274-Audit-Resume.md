# Resume the non-RS274 audit and GPT collection

## September 22 user-requested stop after the current run

The user requested stopping future processing near the weekly usage allotment.
**Do not launch any additional submissions or restart the queue until explicitly
asked to resume.** The sole active submission, **IGES C++ / Sol Max**, launched
at 2026-09-23 00:54 UTC from `3330986`, is allowed to finish generation and grading.
Its local ledger is `work/non-rs274-audit/runs/iges-cpp-gpt-5.6-sol-max/`.
Preserve the resulting source, transcript, usage and grade; independent review
remains required before publication. The reviewed checkpoint remains **69/112**
until that work is complete. Swap changes remain deferred.

The scratch dispatch gate and continuation state record this explicit stop.
Earlier serial-resume authorization is archived in `queue-history/user-stop-*`;
all older next-run instructions below are historical and superseded by this stop.
There is no recurring automation, and no reset-credit redemption, purchase or
push is authorized.

## September 22 Sol Max iCalendar Python and 69-result checkpoint

Sol Max iCalendar Python retry UID `01d6a652-c853-4e4c-82e6-675c1624cbe6`
completed voluntarily from `deb5c75`. Its original **463/467** score under
3.0.4 is preserved; the independently reviewed retained-source regrade is
**466/467** under **ICal 3.0.5**, with one genuine missing VEVENT ADD diagnostic.
Three original failures shared a zero-SEQUENCE CANCEL fixture prerequisite.
The earlier quota-interrupted attempt `6e2b3003-39b1-4db7-ac50-1d93272be2a3`
is preserved and remains excluded.

Tests-only commit `6bd747a` corrects six CANCEL cases without changing their
IDs or the 467-case denominator. The reference passes 467/467. A strict
sequence control improves 3/6 to 6/6; three negative controls each fail their
named property check even with an unrelated warning present. Nine serial
regrades preserve all 461 untouched outcomes per source. All eight prior
scores remain unchanged. All 28 model inputs and reference code are frozen;
full previous publication payloads and audit chains remain available. See
`docs/validation/ICal-3.0.5.md` and its scratch migration directory.

The final source comprises six standard-library/local Python files. Actual
schema, recurrence, DST, duration and CLI assertions are corroborated, but the
last range-order edit lacks a targeted range regression afterward. The final
complete-implementation claim exceeds measured coverage. Accounting commit
`f0f3dbb` recognizes one exact display-only exit-code suffix after an awaited
command, preserving the conservative evidence checks and v2 definition.
The corrected count is **230 calls** (229 canonical actions plus one rejected
command). Raw null usage remains preserved in the regrade audit. There are
**104,099 reasoning tokens within 202,566 output tokens**, 35,463,654 input
tokens including 34,944,896 cached tokens, and a **$20.104310** API-equivalent
estimate. No inference cost is added by regrading.

Coverage is **69/112** (Astra 28, Sol 20, Terra 12, Luna 9), leaving **43**
cells: 39 pending and four quota retries. Qualifying estimates total
**$397.708987**; excluded attempts remain **$54.862522**. These are not
subscription charges. The checkpoint preserves all 60 unrelated completed
rows and all seven excluded attempts; eight prior ICal rows change only the
scoring version, publication hash and audit link.

Both dashboards pass the full migration comparison: **1,845 runs and
1,173,853 test rows**, with exactly one added run and 467 added rows. All
unrelated rows are preserved except expected run-index shifts; unique test
identities remain 20,550. The streamed validation takes 162.03 seconds, peaks
at 55,152 KiB RSS under a 512 MiB address-space cap, and records zero swaps.
The build takes 35.97 seconds and peaks at 37,264 KiB, also without swapping.
All 65 validator controls pass, including an explicit SHA-bound allowance for
the approved null-to-230 tool-count correction; every non-tool usage field
remains fixed. Independent provenance review preserves 1,864 unrelated
publication files, 955 prior audit files and all eight prior target payloads.
The known ancillary CSV newline normalization is documented and untouched.

The next selected cell is **Sol Max / IGES C++**. Use a fresh ordinary-usage
check and the guarded serial launcher. Continue one submission through
generation, grading, independent review, local publication, bounded dashboard
validation and commit before starting another. Swap is deferred while the
user is away. No recurring follow-up was created, and no reset credit,
purchase or push is authorized. Generation evidence is in
`work/non-rs274-audit/runs/ical-py-gpt-5.6-sol-max/`.


## September 22 Sol Max iCalendar Rust and 68-result checkpoint

Sol Max iCalendar Rust completed voluntarily from `efc4799`, UID
`0ca96516-ffc9-44c0-a15b-56718bae72c7`, and is independently reviewed and published
locally at **461/467** under unchanged ICal **3.0.4**. Six failed observations
form four families: EXRULE wrongly excludes an unmatched initial DTSTART in two
cases; VEVENT CANCEL STATUS and ADD RECURRENCE-ID checks are omitted; and orphan
validation covers events but misses both todos and journals. All six tests reach
their intended behavioral assertions under the frozen public requirements. No
new scoring repair is needed.

After the final source edit, item 191 passes six substantive unit tests and a
fresh release build, including the late byte-level unfolding fix for split UTF-8.
Earlier CLI schema assertions precede late edits; other examples merely print
results or exit codes. Clippy and rustfmt were unavailable, so neither is claimed
as passing. The final complete-implementation claim overstates the remaining
defects. All ten package/source files (188,775 bytes) are retained; the model
removed its temporary fixtures and build artifacts before submission.

The accounting correction in `8b157de` recognizes duplicate-target patch
verification failures through the existing conservative runtime/AST guards.
Independent census and the corrected parser agree on **188 tool calls**:
105 commands, 80 file changes and three rejected patches. A separate syntax
failure occurs before execution and adds zero. The raw unavailable metric and
complete first publication are preserved in
`regraded_results/tool-counts/2026-09-22/0ca96516-ffc9-44c0-a15b-56718bae72c7.json`.
All non-tool usage is unchanged: **79,447 reasoning tokens** within 166,339
output tokens and a **$16.243050** API-equivalent estimate. The fix passes
71 relevant tests and 42 subtests, Ruff and strict Pyright; the latter was run
on the host because the sandbox did not expose the virtual environment's
installed pytest to Pyright. See `docs/operations/Telemetry-Accounting.md`.

Coverage is **68/112** (Astra 28, Sol 19, Terra 12, Luna 9), leaving **44** cells
(39 pending and five quota retries). Qualifying estimates total **$377.604677**;
excluded attempts remain **$54.862522**. These estimates are not subscription
charges. Both dashboards are verified: all 1,843 prior main rows and 1,172,919
prior test rows are preserved, apart from expected run-index shifts, and exactly
467 matching cases were added. Build/validation peaked at 36,988/26,616 KiB RSS
with zero swaps under 512 MiB caps, taking 35.65/93.93 seconds. The resulting
dashboard has 1,844 runs and 1,173,386 test rows. Checkpoint comparison preserves
all 67 prior completed rows and all seven excluded attempts exactly.

Commit before the next selected cell,
**Sol Max / iCalendar Python**, using a fresh usage check and a fresh attempt.
Its excluded quota attempt is `6e2b3003-39b1-4db7-ac50-1d93272be2a3`; preserve it
and use the serial launcher's explicit retry/expected-UID guards.

Continue one submission at a time through generation, grading, review,
publication and commit. Swap remains deferred because the user is away; reporting
stays bounded in memory. No scheduled follow-up, credit redemption, purchase or
push is authorized. Current evidence is in
`work/non-rs274-audit/runs/ical-rs-gpt-5.6-sol-max`.

## September 22 Sol Max iCalendar JavaScript and 67-result checkpoint

Sol Max iCalendar JavaScript completed voluntarily from `d2c020e`, UID
`34044a93-8006-4bd3-80dd-38529c677482`, and is reviewed and published locally at
**462/467** under ICal **3.0.4**. The raw **458/467** grade under 3.0.3, source,
transcript and usage remain unchanged. Five remaining observations represent
four families: missing VEVENT CANCEL STATUS validation, missing METHOD:ADD
prohibition, orphan membership checked before EXDATE exclusions, and missing
orphan checks for both todos and journals. Independent review corroborated
selected final semantic assertions but found that the complete-CLI claim
overstates diagnostic coverage; one pipeline's exit status could mask its count
assertion and is not credited as proof of that assertion.

Tests-only commit `2423b39` replaces three invalid component-free calendar
fixtures, accepts orphan diagnostics in parse or expand, and leaves ambiguous
ADD property metadata unscored. All 28 assembled inputs and all reference sources
are unchanged. The reference passes **467/467**. Seven focused cases change from
**0/7 to 7/7** for a control combining three permitted policies; four negative
controls still fail only their intended assertions. All seven retained-source
regrades preserve **460 unaffected outcomes** each. Astra C++ and JavaScript
remain **466/467**, Astra Python **467/467**, Astra Rust **465/467**, Terra Python
**448/467**, and Sol C++ **464/467**. Sol JavaScript gains four justified points.
Complete prior publication payloads and audit history are retained. See
`docs/validation/ICal-3.0.4.md` and the scratch directory
`work/non-rs274-audit/ical-3.0.4-validation/`.

Accounting matches the retained session: **170 tool calls** (120 commands and
50 file changes), **88,969 reasoning tokens** within 176,724 output tokens, and
a **$16.879538** API-equivalent estimate. Coverage is **67/112** (Astra 28, Sol 18,
Terra 12, Luna 9), leaving **45** cells (40 pending and five quota retries).
Qualifying estimates total **$361.361627**; excluded attempts remain
**$54.862522**. These are not subscription charges, and regrading made no model
calls. Checkpoint comparison preserves 60 unrelated completed rows and all seven
excluded attempts exactly; the six prior ICal rows change only scoring version,
publication hash and regrade-audit link.

Both dashboard checks passed: **1,843 runs and 1,172,919 test rows**, with all
unrelated rows preserved apart from run-index shifts. The global unique count
is 20,550: the two renamed cases add eight language-specific identities while
historical runs retain the old names. Build/validation peaked at 37,500/53,356 KiB
RSS with zero swaps under 512 MiB limits, taking 36.09/162.86 seconds. Evidence
is `ical-3.0.4-validation/dashboard-validation.json` in the scratch directory.

Commit this checkpoint before the next selected cell,
**Sol Max / iCalendar Rust**, with a fresh account-capacity check. Continue
one submission at a time through review, publication and commit. The user is
away, so swap remains deferred pending local sudo authentication; use bounded
memory for reporting. The parallel queue remains disabled. No scheduled
follow-up, credit redemption, purchase or push is authorized. This run's ledger
is `work/non-rs274-audit/runs/ical-js-gpt-5.6-sol-max`.

## September 22 Sol Max iCalendar C++ and 66-result checkpoint

Sol Max iCalendar C++ completed voluntarily from `2d0c34c`, UID
`412d4464-0aed-4a09-83c5-cfdb74e5b30e`, and is reviewed and published locally at
**464/467** under ICal **3.0.3**. Its raw **463/468** grade under 3.0.2, source,
transcript and usage are preserved. Three remaining observations represent two
defect families: EXRULE wrongly excludes an unmatched initial DTSTART in two
cases, and METHOD:ADD omits the forbidden RECURRENCE-ID check. Final builds and
bounded sanitizer smoke checks pass; local functional checks mainly assert
successful execution and JSON syntax, not complete semantic outputs.

The tests-only correction is committed as `02335a6`: supply the RFC-required
DTSTART on the no-METHOD cancelled override, retaining its cancellation
assertions, and remove the missing-TRIGGER case's undocumented recovery/warning
policy. Public inputs and reference implementations are unchanged. The reference
passes **467/467**; a strict reader passes the repaired cancellation fixture,
while a false cancellation flag still fails its boolean assertion. All six
retained-source regrades are complete: Sol C++ **464/467**, Astra C++ **466/467**,
Astra JavaScript **466/467**, Astra Python **467/467**, Astra Rust **465/467** and
Terra Python **448/467**. Each preserves all **466 unaffected outcomes**; old
publication payloads and audit history remain intact. See
`docs/validation/ICal-3.0.3.md` and
`work/non-rs274-audit/ical-3.0.3-validation/` for authority and measured controls.

Accounting matches the retained session: **247 tool calls** (142 commands,
101 file changes, three rejected patches and one rejected cleanup request),
**96,801 reasoning tokens** within 188,251 output tokens, and a verified
**$18.577074** API-equivalent estimate. Coverage is **66/112** (Astra 28, Sol 17,
Terra 12, Luna 9), leaving **46** cells (41 pending and five quota retries).
Qualifying estimates total **$344.482089**; excluded attempts remain
**$54.862522**. These are not subscription charges; regrading made no model calls.

Dashboard migration validation **passed**: 1,842 runs and 1,172,452 test rows,
with unrelated records unchanged, all six targets matching their linked grades,
and historical publications preserved. The streaming check peaked at 52,124 KiB
RSS under a 512 MiB limit, with zero swaps. Its exact identity comparison retains
the removed alarm test in historical runs; the global unique count remains
20,542. Evidence is `ical-3.0.3-validation/dashboard-validation-v2.json` beneath
the scratch directory above. Commit before the next selected cell,
**Sol Max / iCalendar JavaScript**, with a fresh account-capacity check. The user
is away and authorized continued useful collection, still **one submission at a
time**. Swap remains deferred pending the user's local sudo authentication;
continue bounded-memory reporting. The parallel queue stays disabled, and no
scheduled follow-up, credit redemption, purchase or push is authorized. This
run's ledger is `work/non-rs274-audit/runs/ical-cpp-gpt-5.6-sol-max`.

## September 22 Sol Max GEDCOM Rust completion

Sol Max GEDCOM Rust completed voluntarily from `a0e6b0f`, UID
`769bd4eb-a204-4d83-b59e-54c22bb4f926`, and is reviewed and published locally at
**212/212** under unchanged GEDCOM 4.0.3. All seven optional-identifier cases
pass. Independent source/claim review found no publication blocker or scoring
repair. The final command passes eight release-mode unit tests and asserts all
four CLI actions, exact dataset/attachment round trips, independent Python
DEFLATE attachment bytes, and malformed-level error code/line. Only `.gitignore`
is added afterward. The captured Cargo build caches remain intact; the source
hash covers all 329 files and five empty directories (58,105,994 file bytes).

Accounting matches the retained session: **92 tool calls** (62 commands, 28 file
changes and two rejected patches), **48,613 reasoning tokens** within 111,796
output tokens, and a verified **$10.341348** API-equivalent estimate. This is
not a subscription charge. The local eight tests are separate from the 212
hidden cases, and neither count represents that many independent capabilities.

Coverage is **65/112** (Astra 28, Sol 16, Terra 12, Luna 9), leaving **47** cells
(42 pending and five quota retries). Qualifying estimates total **$325.905015**;
excluded attempts remain **$54.862522**. Sol Max GEDCOM now has C++ 212/212,
JavaScript 205/212, Python 205/212 and Rust 212/212.
Both dashboards are verified: all 1,840 prior main rows and 1,171,778 prior test
rows are preserved, except expected run-index shifts; 212 exact new cases were
added. Build/validation used 37,100/33,064 KiB peak RSS, zero swaps, and
34.21/92.15 seconds under 512 MiB limits.

Commit this checkpoint before **Sol Max / iCalendar C++**, after a fresh usage
check. Continue one submission at a time. Swap remains deferred; no scheduled
follow-up or push is authorized. Use the objective helper and independent
content review documented below, then publish, validate and commit before the
next dispatch. This run's ledger is
`work/non-rs274-audit/runs/gedcom-rs-gpt-5.6-sol-max`.

## September 22 Sol Max GEDCOM JavaScript completion

Sol Max GEDCOM JavaScript completed voluntarily from `2a4d781`, UID
`886ad695-c9d1-42ad-8af2-f9e6179eddc4`, and is reviewed and published locally at
**205/212** under unchanged GEDCOM 4.0.3. All seven failures share the unconditional
identifier requirement at `gedcom.js:971`: the supplied specification explicitly
allows unreferenced records to omit their cross-reference IDs. The seven valid,
pointer-free fixtures cover different record types. Report one defect family
with seven observations, not seven independent bugs. Independent review found
no invalid test or required scoring change.

The final regression asserted all four CLI actions and malformed-level rejection
after the last source edit. Earlier independent Python ZIP, Unicode, CRC and
deep-tree checks are real assertions but were not all repeated after late edits.
Accounting matches retained evidence: **90 tool calls** (62 commands and 28 file
changes), **42,567 reasoning tokens** within 90,284 output tokens, and a verified
**$7.215988** API-equivalent estimate. Raw results, source and sessions are intact.

Coverage is **64/112** (Astra 28, Sol 15, Terra 12, Luna 9), leaving **48** cells
(43 pending and five quota retries). Qualifying estimates total **$315.563667**;
excluded attempts remain **$54.862522**. These are not subscription charges.
Both dashboards are verified: all 1,839 prior main rows remain unchanged; all
1,171,566 prior test rows remain unchanged except the expected run-index shift,
and the 212 added cases match publication. Build/validation used 37,268/33,312
KiB peak RSS, zero swaps, and 34.19/93.89 seconds under 512 MiB limits.

Commit this checkpoint before launching **Sol Max / GEDCOM Rust**, after a fresh
account-capacity check. Continue one submission at a time. Swap remains deferred,
the parallel queue stays disabled, and no schedule or push is authorized.
The local `work/non-rs274-audit/objective_review.py` helper now verifies factual
accounting/provenance after `prepare_review.py` and verified host worker exit.
It matched two prior reviewed runs and passed 15 failure controls, Ruff and
strict Pyright; root reviewed its code. It writes no approval or content verdict,
and refuses to overwrite records. Independent content review remains required.
See local `OBJECTIVE-REVIEW.md` and `objective-review-validation.json` beside it.
This run's ledger is `work/non-rs274-audit/runs/gedcom-js-gpt-5.6-sol-max`.

## September 22 Sol Max GEDCOM C++ completion

Sol Max GEDCOM C++ completed voluntarily from `2358b55` under unchanged
GEDCOM 4.0.3 at **212/212**, UID `f1262eca-0f6a-488e-80e4-9846ff776472`.
Root accounting and an independent content review found no publication blocker
or new scoring repair. The final source was recompiled in both ordinary and
sanitizer builds; four final smoke requests asserted return codes and empty
stderr. Earlier printed checks and pre-edit random archive checks are not
represented as exhaustive final-source verification.

The raw result records **149 tool calls** (90 commands, 57 file changes and two
rejected requests), **47,263 reasoning tokens** within 105,728 output tokens,
and a verified **$11.980829** API-equivalent estimate. Original source, transcript,
raw grade and accounting remain unchanged. The reviewed collection is now
**63/112**, with publication and both dashboard validations complete, leaving
49 cells (44 pending and five quota retries). Qualifying estimates total
**$308.347679**; excluded attempts remain **$54.862522**.

Both dashboard checks passed. The main dashboard preserves all 1,838 old rows;
the per-test dashboard preserves all 1,171,354 old rows except the expected
run-index shift and adds exactly 212 matching cases. Build/validation used
37,208/32,564 KiB peak RSS, zero swaps, and 34.92/90.74 seconds under 512 MiB
limits. Commit this checkpoint before the next selected cell,
**Sol Max / GEDCOM JavaScript**. The serial
launch gate remains enabled and the old parallel queue remains disabled. Swap
is still deferred. No scheduled follow-up was created: automatic approval review
rejected a persistent 15-minute launch/commit schedule because explicit
scheduling authorization was missing. An asynchronous approval question is
pending; continue work within the active session without bypassing that rejection.
Evidence lives in `work/non-rs274-audit/runs/gedcom-cpp-gpt-5.6-sol-max`.

## September 22 continuation while the user is away

The user explicitly asked to keep collecting useful results before the upcoming
account reset, retaining **one submission at a time**. The swap increase is
deferred because local sudo authentication requires the user; it must not block
collection. The prepared script is `work/increase-swap-to-8g.sh`, but the active
swap remains 4 GiB until a later successful host verification. Continue using
bounded-memory reporting. No credit redemption, purchase or push is authorized.
At 06:29 CDT, the account reported 26% weekly usage and a September 26,
05:52:22 CDT reset. Recheck live capacity before every new dispatch.

The fresh Sol Max BibTeX Rust attempt completed normally under 1.2.5 at
**379/386**, UID `18469fec-1314-4b02-93eb-6b522084e9c6`, generated from
`d6dbb7a` in `eval2`. The earlier provider-capacity attempt remains excluded and
hash-preserved, with its prior ledger archived under its original UID. All eight
canonical-style parity cases pass. Seven failures represent five causal
families: merged database/function namespaces (two observations), past-end name
selection, extra commas in names, whitespace trimming (two observations), and
EOF buffering. The supplied WEB and existing authority hierarchy support the
expectations; this result requires no scoring change.

The final transcript supports 23 release-mode unit tests, a release build,
four-style smoke fixtures and an aux workflow after the final source edit.
Local whitespace tests assert the wrong behavior, so those successes do not
establish complete canonical semantics. Accounting matches preserved evidence:
**280 tool calls** (183 commands, 95 file changes and two rejected patches),
**87,700 reasoning tokens** within 174,079 output tokens, and a **$21.255390**
API-equivalent estimate. The reviewed collection advances to **62/112**, leaving
50 cells (45 pending and five quota retries). Qualifying estimates total
**$296.366850**; excluded attempts remain **$54.862522**. The next selected cell
is **Sol Max / GEDCOM C++**. Publication and dashboard verification are complete;
commit this checkpoint before dispatching it. All 1,170,968 previous test rows
remain unchanged apart from the insertion's run-index shift, and all 386 added
rows match the new publication. The main dashboard preserves all 1,837 previous
rows. Build/verification peaked at 36,840/33,624 KiB RSS with zero swaps under
512 MiB limits. Evidence, source/transcript review and preserved prior-attempt
records are in `work/non-rs274-audit/runs/bibtex-rs-gpt-5.6-sol-max`.

## September 21 LAS scoring correction and 61-result checkpoint

Luna Max LAS Rust completed normally under 2.0.4 at 215/223 (UID
`d0a1d8fc-a69f-451f-81a1-f778b3758942`). Its raw source, grade, transcript and
usage are preserved. Its reviewed local publication now scores **219/223** under
the tests-only LAS 2.0.5 migration. The remaining four failures share an incorrect
superseded-record interpretation; they are not four independent bugs. Review
also notes an unscored static ExtraBytes unused-slot validation gap. Its 90 tool
calls, 50,492 reasoning tokens within 119,122 output tokens, and **$0.416148**
API-equivalent estimate match the preserved session.
The four descriptor/storage-free zero-waveform positives were ambiguous under
the full public corpus. Earlier statements below calling those failures model
defects, or saying no rubric repair was needed, are withdrawn. See
[LAS 2.0.5](../validation/LAS-2.0.5.md) for the public basis and controls.
All 16 saved-source comparisons and publication reviews are complete. Nine
scores gain exactly four passes; seven stay unchanged. Each source preserves
all 219 unaffected test outcomes. Historical publications and their audit chains
remain embedded in separate regrade records. The tool-count audit for Luna C++
also recovers **91 calls** (88 canonical actions plus three explicit rejected
requests); its previously unavailable count came from older rejection parsing,
not the later display-expression parser change. Original generation bytes,
non-tool token usage and costs remain unchanged.

Coverage is **61/112**: Astra 28, Sol 12, Terra 12 and Luna 9. **51 remain**
(45 unstarted, five quota retries and one provider-capacity retry). The next
selected cell is **Sol Max / BibTeX Rust**, retrying the preserved capacity
failure below with a fresh output directory and `--retry-excluded`. Inspect
worker state and fresh account capacity before dispatch; do not restart the
parallel queue. Finish generation, grading, content/accounting review,
publication and local commit for each submission before starting another.
Qualifying estimates total **$275.111460**; seven excluded attempts total
**$54.862522**. These are API-equivalent estimates, not subscription charges.
The one-submission gate remains in force. Swap stays at 4 GiB; use only the
bounded-memory dashboard writer and streaming verification.

The completed migration dashboard has 1,837 runs and 1,170,968 test rows. A
streaming comparison checks every previous row, all 16 changed/new LAS
projections, exact counts and unique nodes. Unrelated records are unchanged
apart from the insertion's run-index shift. The build used 37,172 KiB peak RSS
in 36.37 seconds; verification used 53,272 KiB in 172.24 seconds. Both ran under
a 512 MiB address-space limit with zero swaps. Tracked non-target publications
and all older audit files remain unchanged. Evidence and the checked manifest
are in `work/las-zero-waveform-followup`; the portable measured summary is
[LAS 2.0.5 regrades](../validation/LAS-2.0.5-regrades.json).

## September 21 continuation

At 16:27:49 CDT, the host exhausted RAM and all 4 GB of swap during overlapping
reporting work. The kernel killed a Python process, and the ChatGPT app scopes
ended immediately afterward. The OS did not restart (boot remains September 16).
The Terra LAS JavaScript generation and review had already finished; its raw
result, local publication and 58-result checkpoint survived. No next generation
had started. The main dashboard was refreshed, but the 1.25 GB per-test aggregate
remained the previous September 17 file. Reporting now streams each expanded
test row into a sibling temporary file and atomically replaces the destination
only after validation succeeds. A full recovery build under a 512 MiB address
space limit produced 1,170,299 records across 1,834 runs in 36 seconds, with
37,224 KiB peak resident memory and no swaps. Relevant kernel/app evidence and
recovery logs are in `work/non-rs274-audit/incident-20260921-oom`. Keep these
operations sequential and never load the full per-test aggregate into Python
for validation. This reporting change does not alter scoring or model inputs.
All 1,170,076 preceding test rows were then compared with bounded memory:
their contents are unchanged except the expected run-index shift after the new
publication; all 223 added rows match it. The comparison used 25,520 KiB peak
resident memory. Twenty-seven targeted regression tests, strict Pyright, Ruff
and independent review passed. Recovery is complete; no eval rerun is needed.

The user renewed the instruction to continue, still one submission at a time.
Weekly capacity was checked at 7% used (93% remaining). The September 17
capacity hold is historical. Sol Max / BibTeX Rust was launched from `c3e5f0c`
under BibTeX 1.2.5, UID `7a1a5ac4-26c5-474f-872a-5dbfe55cc071`, but the provider
ended it after 259 seconds with `server_overloaded` / “Selected model is at
capacity.” It had only read references and produced no source. Its 386 grader
setup errors are diagnostic; they are not a completed 0/386 model score.

Independent review and original/session accounting agree: 555,000 partial tokens,
4,300 reasoning tokens within 5,803 output tokens, 15 tool calls, and a $0.633693
API-equivalent estimate. Raw artifacts are unchanged. Its ledger `omitted.json`
uses **infra_provider_capacity**, distinct from the five **infra_usage_cap**
attempts. The original and structured failure evidence are included in the
committed excluded-attempt snapshot. A future retry must use a fresh generation.
The local `dispatch_safety.py` retry guard now recognizes this exact status only
with a matching preserved capacity-failure terminal event; real provider/quota
and negative-control checks, Ruff and strict Pyright passed. Preserve the local
helpers and ledgers with the raw artifacts.

Terra Max / LAS JavaScript subsequently completed normally and is reviewed and
published locally at **223/223** under unchanged LAS 2.0.4 tests. UID
`a5f6ae06-0043-4315-b357-61658398ef5b`; generation revision `8de6fef`.
Independent review found a general implementation and supported completion
claims, with qualifications for failed local test transport and unavailable
utilities, a misdirected final negative probe, and focused rather than broad
local retesting after its final waveform validation adjustment. The final source
passed all 223 hidden cases. Preserved events match 68 tool calls, 53,623 reasoning
tokens within 98,113 output tokens, and the recomputed **$3.236420** API-equivalent
estimate. Isolation, prompt/test hashes, and pinned images all match the study.
No scoring repair, telemetry correction, or regrade was required.

Terra Max / LAS Rust then completed normally at **223/223** under LAS 2.0.4,
UID `a0ec7949-71be-4442-8e84-2ed3d48ddee0`, generated from `c747ec5`.
Independent review supports its general standard-library implementation and final
build claim. Initial compile errors and a UUID panic were corrected; rustfmt was
unavailable. A late chained negative probe can mask an earlier failure, and the
final waveform error-offset edit was rebuilt without a later execution probe.
The hidden suite grades that final source. Accounting preserves 46,504 reasoning
tokens within 94,375 output tokens and a **$3.038195** API-equivalent estimate.
Its original tool count was conservatively unavailable: a direct rejected patch
used a display-only `typeof`/`JSON.stringify` expression outside the parser's
accepted forms. A narrow AST extension proves **70 tool calls** (68 canonical
actions plus two explicit pre-item rejections). It does not execute generated
JavaScript or admit conditional tool requests. Focused tests, strict Pyright,
Ruff and independent review validate the extension. The separate
[tool-count audit](../../regraded_results/tool-counts/2026-09-21/a0ec7949-71be-4442-8e84-2ed3d48ddee0.json)
preserves the original usage and complete previous publication; scores, source,
generation bytes, token totals and costs are unchanged. No regrade was needed.

Luna Max / LAS JavaScript completed normally after 53 minutes at **215/223**,
UID `5f2d7e9d-aa02-4b3c-85d9-05b513d912ce`, generated from `d03c8d6` under
unchanged LAS 2.0.4. The initial review incorrectly treated the four missing
waveform-metadata positives as model defects; that interpretation is withdrawn
above. After the 2.0.5 fixture correction, the unchanged source scores **219/223**.
The four remaining observations measure missing internal waveform packet
interval checks at two boundaries through both CLI actions, not four independent
bugs. Luna C++ has the same remaining failure family. Local all-format smoke
claims are supported but always supplied waveform
metadata; several negative probes targeted the wrong condition, and later source
changes received focused checks rather than another all-format sweep. Preserved
evidence establishes **73 tool calls** (72 canonical actions plus one rejected
patch), 57,817 reasoning tokens within 103,077 output tokens, and a **$0.315449**
API-equivalent estimate. The review notes retain these limitations.

Before Luna Rust and the 2.0.5 migration, coverage was **60/112**, with 52 cells
needing qualifying results. The current checkpoint above supersedes that count.
Collection covers all seven non-RS274 tasks, including their tests-only repairs;
the public-input revision remains deferred. The previous four-worker queue
remains disabled.

## Historical checkpoint — September 17, 2026

Coverage is **57/112 reviewed local publications** (Astra 28, Sol 12, Terra 10,
Luna 7); **55 remain**. No generation is active. The sequential authorization
below remains in effect, but new dispatch is held for capacity: the account
reported **99% weekly usage** at 06:14 CDT, with its scheduled reset at
**September 19, 04:41:46 CDT**. Recheck actual limits before spending more model
usage. No reset credit or paid purchase is authorized. The next selected cell
is **BibTeX Rust / Sol / Max**, after confirming this checkpoint and worker state.
Do not launch a duplicate JavaScript run or restart the parallel queue.

Sol Max BibTeX JavaScript completed normally with original grade 314/386. Its
review exposed another shared scoring prerequisite. The supplied authoritative
WEB discards pending output at EOF, contrary to the summary's must-flush prose;
the existing public authority hierarchy resolves the conflict. The private
**BibTeX 1.2.5** repair explicitly flushes semantic probes and corrects the one
EOF test. Corrected reference 386/386, old-reference mutation 385/386, five native
oracle probes, strict lint/type checks and independent review support the fix.
The submission now scores **383/386**: 69 false failures disappear, while two
namespace observations and one past-end-name defect remain. Public inputs,
submitted source and generation records stay unchanged.

The run UID is `acd96c79-8fa0-402c-b3ee-875a25629538`; usage is 178 tool calls,
81,166 reasoning tokens (within 137,070 output tokens), and a **$14.191125**
API-equivalent estimate. Content review corroborates final syntax/style checks
but qualifies printed probes and one locally failed assertion hidden by a later
successful cleanup command. All eight official canonical-style parity cases pass.
The original 314/386 report is preserved, with a separate official regrade.

The seven other retained qualifying BibTeX submissions were regraded one at a
time; each loses exactly the erroneous EOF point, with all other 385 outcomes
unchanged. Complete previous publication payloads and audit hashes are retained.
See [BibTeX 1.2.5 validation](../validation/BibTeX-1.2.5.md) and the refreshed
[score matrix](../validation/non-rs274-2026-09-12/README.md).
Current qualifying estimates total **$268.105248**; the six excluded attempts
remain **$54.228829**. These estimates are not subscription charges.

The scoring fix is commit `ab4e09f`; publication/checkpoint changes follow it
locally. No push was made. Validation, native probes and serial regrade logs are
in `work/bibtex-eof-followup`; original generations and the review ledgers remain
in the locations below. `LAUNCHES_PAUSED` records the capacity hold and next cell.
The historical progress paragraphs below explain earlier checkpoints; the
current matrix and this section supersede their old counts and scoring versions.

## Current authorization: serial work resumed

On 2026-09-16 (local time), the user authorized continuation with **one
submission at a time**. Finish the four retained reviews sequentially before
generating more submissions, then launch exactly one selected missing cell,
wait for its worker to exit, and review/publish or explicitly exclude it before
starting another. No parallel collection queue is authorized. The local
`work/non-rs274-audit/SERIAL_RESUME.json` records this instruction and the
hash-preserved archive of the prior pause/queue state. A remaining pause marker
is a dispatch gate while saved reviews are completed, not a prohibition on
the newly authorized review work.

All four workers from the September 12 pause exited normally. Their original
scores are GEDCOM Rust 212/212, ICal C++ 466/468, ICal JavaScript 467/468, and
ICal Rust 465/468; review and publication status must be read from the current
ledger. The completed local drain inventory is `final-drain-results.json`.
The September 12 snapshots below remain historical checkpoints.

The four retained submissions have now been reviewed and published locally,
bringing coverage to **47/112**. Their raw scores are unchanged. The ICal
failures are isolated diagnostic omissions: all three languages miss the
EXDATE/orphan warning, C++ and Rust miss the absent alarm-trigger warning, and
Rust also omits the forbidden `RECURRENCE-ID` diagnostic for iTIP ADD. Reviews
checked these expectations against the supplied application contract and RFCs;
none justified another scoring change. Full accounting and isolation checks
passed for all four. Independent content reviews and publication checks are
retained in each local ledger directory. The four original API-equivalent
estimates sum to **$31.597644**; these are existing generation costs, not new
inference caused by reviewing them.

The 47-result dashboard check verified that all 1,819 preceding rows remained
unchanged and that four new rows match their publications. Evidence is in
`work/non-rs274-audit/dashboard-47-validation.json`.

The first fresh serial generation, MARC21 C++ / Astra / Max, completed normally
and is reviewed/published at **2900/2900**, bringing coverage to **48/112**.
Its 94 internal regression checks and 48 CLI checks are corroborated, along
with 40 underlying tool calls, 12,274 reasoning tokens, and a $5.547096 recorded
API-equivalent estimate. The unchanged scoring rubric and grader image were
verified. Its UID is `dfe849c7-c762-4104-b6dc-e1a33cbf617e`.
MARC21 JavaScript / Astra / Max then completed normally and is reviewed and
published at **2900/2900**, bringing coverage to **49/112**. Its 30 self-test
groups and isolated-output-copy checks are corroborated, together with 39
underlying tool calls, 12,048 reasoning tokens, and a $6.413580 recorded
API-equivalent estimate. Its UID is `70e4aee1-6323-4865-8bbe-a69903f61149`.
MARC21 Rust / Astra / Max completed normally and is reviewed and published at
**2900/2900**, bringing coverage to **50/112**. Its release build, nine Rust tests
and 180 CLI requests are corroborated, together with 34 underlying tool calls,
10,166 reasoning tokens, and a $4.844408 recorded API-equivalent estimate.
The self-test correction from `007="zz"` to invalid `007="zx"` follows explicit
examples in the supplied documentation; it did not alter runtime validation.
Its UID is `acad2564-7e18-41b0-85cd-019a5352a0fc`.
IGES C++ / Astra / Max completed normally and is reviewed and published at
**259/261**, bringing coverage to **51/112**. Both failures expose the same
zero-count Hollerith misconception separately in the reader and writer:
the former accepts `0H`, and the latter emits it for empty Global strings.
The supplied nonzero-count rule and legal NULL controls support both tests;
this is one shared defect, without broad failure amplification. Final normal
and sanitizer checks are corroborated, but self-roundtrip consistency misses
this symmetric defect. External CAD samples were unavailable, as the final
message acknowledges. Usage matches preserved events: 53 underlying tool calls,
31,221 reasoning tokens, and a $10.873110 recorded API-equivalent estimate.
Its UID is `55906e04-d378-4f80-8b79-150a110517d1`.
IGES JavaScript / Astra / Max completed and is reviewed/published at **260/261**
under the tests-only IGES **1.0.18** patch, bringing coverage to **52/112**.
Its original 259/261 exposed a remaining invalid Face fixture; the corrected
test uses a validated topology and directly observes Logical encoding.
Reference checks, deliberate mutations and independent review support the fix.
Exactly one outcome changes; the real `0H` reader defect remains. The source,
public inputs and generation accounting remain unchanged: 41 underlying tool
calls, 23,051 reasoning tokens, and a $8.583752 API-equivalent estimate.
Its UID is `97909084-fe80-42ff-b359-2a30798f8f67`.
Existing Astra IGES Python and C++ were regraded sequentially to 1.0.18 and
remain 261/261 and 259/261, respectively, with all individual outcomes unchanged.
Original grades and complete prior publication/audit chains are preserved.
See [IGES 1.0.18 validation](../validation/IGES-1.0.18.md).
IGES Rust / Astra / Max then completed normally, bringing coverage to
**53/112** and completing all **28 Astra cells**. Its original 245/261 exposed
invalid/conflicted appendix fields and fivefold repeated parse prerequisites.
The independently reviewed tests-only **1.0.19** repair normalizes those fields
and consolidates fifteen integration cases into three, retaining the assertions
and explicitly changing the denominator from 261 to 249. All model inputs stay
unchanged. Three references pass 249/249 and four mutation controls verify the
retained observations and reduced failure amplification.

Official sequential regrades are Python **249/249**, C++ **247/249**,
JavaScript **248/249** and Rust **247/249**. Rust's two remaining defects accept
illegal `0H` and mishandle a legal trailing default before an empty array.
All 246 unchanged per-case outcomes match each preceding publication. Complete
original records and publication chains are preserved. Rust's release build,
nine unit tests and 232 synthetic CLI requests are corroborated; accounting
matches 56 tool calls, 23,383 reasoning tokens and a $13.159838 API-equivalent
estimate. Its UID is `e81a9c23-e06f-4fe7-8a1e-e39e9941c058`.
See [IGES 1.0.19 validation](../validation/IGES-1.0.19.md).
The rebuilt dashboard contains 1,829 rows: all 1,825 unrelated rows are
unchanged, the three earlier Astra IGES rows change only reviewed scoring or
editorial fields, and the new Rust row matches its publication. Generation
accounting and cohorts are unchanged. Evidence is in
`work/non-rs274-audit/dashboard-53-validation.json`.

LAS JavaScript / Sol / Max completed and is reviewed/published at **219/223**,
bringing coverage to **54/112**. One shared overstrict waveform-metadata
prerequisite causes the four failures in formats 4, 5, 9 and 10; the supplied
specification supports the positive no-waveform cases, so no rubric change is
needed. Final local probes, CLI error checks and syntax checks are corroborated;
external interoperability remains unverified. Its UID is
`2afb5142-8c8a-4e36-b7a9-323a7116324b`.

This run exposed a failed patch omitted from canonical file-change events.
The independently reviewed harness fix recovers **63 tool calls** from 62
canonical items plus the proven rejection, with conservative conflicting-output
and overlap guards. The original null metric remains in the raw result. All
tokens and the **$4.394560** API-equivalent estimate are unchanged, including
37,373 reasoning tokens. A same-version saved-source regrade reproduces every
one of the 223 outcomes and preserves correction evidence in the publication
audit. See [telemetry accounting](Telemetry-Accounting.md).
The 54-result dashboard check confirms all 1,829 preceding rows are unchanged
and the new row matches its publication, with 1,169,081 generated test records.
Evidence is in `work/non-rs274-audit/dashboard-54-validation.json`.

LAS Rust / Sol / Max then completed and is reviewed/published at **219/223**,
bringing coverage to **55/112**. It has the same shared absent-waveform metadata
defect across four formats; public authority supports the tests. Final release
build and CLI probes are corroborated, while `cargo test` ran zero tests and
rustfmt/Clippy were unavailable. Selected synthetic probes do not establish
external interoperability. The current harness correctly recorded **65 tool
calls**, including one rejected patch, directly in the original result; no
backfill or regrade was needed. Usage matches preserved evidence: **28,300
reasoning tokens** and a **$4.592502** API-equivalent estimate. Its UID is
`066b6ee1-e620-41f3-8142-a1702196d614`.
The 55-result dashboard check preserves all 1,830 preceding rows and verifies
the new row against publication; 1,169,304 test records were generated. Evidence
is in `work/non-rs274-audit/dashboard-55-validation.json`.

BibTeX C++ / Sol / Max completed and is reviewed/published at **379/386**,
bringing coverage to **56/112**. Seven focused failures reflect five causes:
shared macro/callable namespaces, past-end name selection, extra name commas,
preamble separators, and output whitespace flushing. All eight official
canonical-style parity cases pass. Supplied authoritative WEB rules support
the failures; no rubric change is needed and there is no broad prerequisite
cascade. Clean builds and sanitizer executions are corroborated. Many local
probes only print output; one visibly preserves trailing whitespace despite
the model's broad passing-check claim, which publication notes qualify.
Accounting matches **123 tool calls**, **45,178 reasoning tokens**, and a
**$11.557364** API-equivalent estimate. Its UID is
`81ffee84-ff8e-47d1-a513-4a2c6b7dfbc0`.
The 56-result dashboard check preserves all 1,831 preceding rows and verifies
the new publication row; 1,169,690 test records were generated. Evidence is in
`work/non-rs274-audit/dashboard-56-validation.json`.

There are **56 cells remaining**, including five excluded quota attempts that
need fresh retries. The 56 qualifying runs total **$253.914123** in recorded
API-equivalent estimates; excluded attempts still total $54.228829. The next
selected submission is BibTeX JavaScript / Sol / Max; inspect its ledger before
launching to avoid a duplicate. Continue one submission at a time.

## Stop condition and current state

On 2026-09-12 the user requested winding down to conserve usage. **Do not
launch new generations, retry excluded attempts, consume a usage reset, or
restart the collection queue until the user explicitly asks to resume.**
`work/non-rs274-audit/LAUNCHES_PAUSED` records this request. The four generations
already running were allowed to finish; their latest disposition is recorded
in [the wind-down snapshot](../validation/non-rs274-2026-09-12/wind-down.json).

To avoid spending more agent usage while waiting, the review subagents were
stopped and the four new full reviews/publications were deferred. A plain local
Python process, `work/non-rs274-audit/finish_inflight.py`, waits only for the four
frozen worker identities and writes `work/non-rs274-audit/final-drain-results.json`
as each exits. **Read that file first if the documentation checkpoint still
shows active workers.** Its launch record and output are `final-drain-launch.json`
and `final-drain.log`. It makes no model calls, starts no evaluations, and does
not grade, review, publish, commit, or change the original artifacts. It exits
after those four workers exit. These processes need the workstation to remain
running; this is not a cloud workflow or scheduled Codex follow-up.

The task was to audit the seven tasks other than RS274, repair misleading
scoring, and fill missing GPT coverage. The test audit and repairs are complete.
The collection targets **112 cells**: Astra, Sol, Terra and Luna at Max, across
seven tasks and four languages, with **one generation per cell**. It does not
target three repeats or additional reasoning levels. At the pause there were
43 reviewed local publications, four active runs, 60 untouched cells, and five
quota retries. Check the snapshot and live ledger before acting on these counts.

All work is committed locally on `main`; no push was made in this phase. The
starting remote revision was `b7e5c1a453c4c3a5575742d624d2bf306764e022`. Preserve
the local commits and artifacts when reconciling future remote changes.

## Read first

- [Audit report and score matrix](../validation/non-rs274-2026-09-12/README.md)
- [Completed results](../validation/non-rs274-2026-09-12/completed-results.json)
- [Remaining coverage](../validation/non-rs274-2026-09-12/remaining-coverage.json)
- [Excluded attempts](../validation/non-rs274-2026-09-12/excluded-attempts.json)
- [Public-input hash manifest](../validation/non-rs274-2026-09-12/public-inputs.json)
- [30 deferred public clarifications](../validation/non-rs274-2026-09-12/public-clarifications.md)
- [Repository instructions](../../AGENTS.md), [author-eval skill](../../.codex/skills/author-eval/SKILL.md),
  [run-eval skill](../../.codex/skills/run-eval/SKILL.md), and
  [build-and-lint skill](../../.codex/skills/build-and-lint/SKILL.md)

Final scoring versions: WordCount **1.0.4**, LAS **2.0.5**, GEDCOM **4.0.3**,
MARC21 **3.0.2**, BibTeX **1.2.5**, ICal **3.0.2**, IGES **1.0.19**. Their
dated changelogs and linked validation notes explain source authority,
reference results, negative controls, permitted alternatives, and exact
retained-submission changes. All 28 assembled model inputs remain unchanged.
Public wording/contract changes are a separate future phase; do not impose
new choices on these saved submissions.

## Local files that Git does not preserve

Repository:
`/home/matthew/Documents/Codex/2026-09-05/ca/CLISpecBench`

Work ledger and helpers:
`/home/matthew/Documents/Codex/2026-09-05/ca/work/non-rs274-audit`

Original generations are under `CLISpecBench/transient_results`. Their sources,
canonical transcripts, richer session JSONL, network logs, usage, and original
test reports are essential. Full regrades, scratch validation, review evidence,
and queue history are under the sibling `work` directory. **A Git clone alone
does not recover these files.** Preserve these directories before moving or
cleaning the workstation. Portable publication/regrade summaries are committed
under `published_results` and `regraded_results`.

Each cell has `work/non-rs274-audit/runs/<task>-<model>-max/launch.json` and
`run.log`. Completed reviews use `review.json` and `evidence.json`; publication
checks may add `publication-review.json`. Use `attempts.result_paths(root,
launch)` to identify the current attempt. Do not select the first matching
`eval*/run*/result.json`: Astra BibTeX Python's valid retry is in `eval2/run1`,
while its excluded older generation remains in `eval1/run1`.

## Read-only status

Run from a normal host terminal, or use an escalated host command in Codex.
The app's sandbox process namespace can hide live worker PIDs.

```sh
cd /home/matthew/Documents/Codex/2026-09-05/ca/CLISpecBench
sg docker -c '.venv/bin/python3 ../work/non-rs274-audit/status.py'
cat ../work/non-rs274-audit/LAUNCHES_PAUSED
git status --short
```

The ledger calls a launched cell without a result `running`; check the actual
worker before concluding it is alive or dead. `dispatch_safety.worker_is_running`
uses PID start ticks and excludes zombies; run it in the host namespace. Result
creation precedes container cleanup, so a result alone does not release a slot.
Do not remove `collection-queue.lock` or kill a PID based on a stale ledger.

At the pause, the four slugs were:

- `gedcom-rs-gpt-6-astra-max`
- `ical-cpp-gpt-6-astra-max`
- `ical-js-gpt-6-astra-max`
- `ical-rs-gpt-6-astra-max`

## Finish existing reviews before generating anything

For each completed but unpublished attempt, inspect its current review/evidence
files, final canonical turn, richer session, source, every failed case, and
network/tool-access audit. Resolve issues by source authority and distinguish
failure clusters from independent bugs. A new ambiguity should be recorded as
a hold before starting another rubric repair campaign.

Objective evidence can be refreshed without calling a model:

```sh
.venv/bin/python3 ../work/non-rs274-audit/prepare_review.py ical-cpp gpt-6-astra > ../work/non-rs274-audit/runs/ical-cpp-gpt-6-astra-max/review-extract.txt
```

This helper does not replace substantive review. `publish_reviewed.py` accepts
an operator-written summary and notes, rechecks telemetry and isolation, and
publishes locally only when the original score uses the current rubric. Use
structured subprocess arguments for summaries/notes read from `review.json`,
not shell interpolation of model text. A stale rubric requires an explicit
saved-source regrade using `regrade_batch.py`/`publish_regrade.py`.

Never execute or import submissions on the host or in their original source
directories. Regrades use read-only original mounts and fresh disposable
copies inside offline Docker. Keep at most two regrade containers.

## Resume with a small budget

The user requested a cost pause. Prefer **one selected cell at a time** after
new authorization, rather than restarting the entire remaining queue.

1. Verify no old queue owns dispatch and no prior worker for the selected cell
   is alive. Review completed attempts first; do not generate duplicates.
2. Preserve the pause marker and prior queue files in a new timestamped
   `work/non-rs274-audit/queue-history/` directory, recording their SHA256 values.
   Existing history is an example; do not overwrite it.
3. Only after explicit authorization, remove the active pause marker and run
   a selected **still-pending** cell. For example, if the inventory still lists
   Sol C++ BibTeX as pending:

```sh
sg docker -c '.venv/bin/python3 ../work/non-rs274-audit/launch_batch.py bibtex --model gpt-5.6-sol --language cpp'
```

4. Restore a pause marker after the selected launcher returns if no further
   dispatch is authorized. Let that generation finish and review it before
   spending more usage. A launch returning successfully means it started,
   not that generation or grading finished.

`launch_batch.py` rejects duplicates, checks committed rubric/harness and
unchanged public input, and requires explicit apps disablement. A quota retry
needs `--retry-excluded`; this archives the exact excluded ledger and starts a
fresh generation. Do not reuse its partial source or change its old score.

The historical `collect_remaining.py --run --max-active 4` queue would dispatch
**all remaining inventoried cells**, pausing on generation/grading errors.
It never publishes automatically. **Do not restart it under the current
one-submission-at-a-time authorization.** It also cannot be used merely to inspect status.
`start_queue.py` opens `collection-queue.log` exclusively, so it cannot be rerun
over the existing log. Before an authorized full-queue restart, archive the old
log, launch record, status, plan, and pause marker with hashes; remove only the
archived active log and resolved pause marker, then run:

```sh
sg docker -c '.venv/bin/python3 ../work/non-rs274-audit/start_queue.py'
```

Do not bypass its queue lock or run a second queue. Four generation slots count
workers until cleanup and exit. If usage is exhausted, stop new dispatch and
preserve failed attempts; no automatic reset or credit purchase is authorized.

## Conditions and accounting to preserve

- Agent image: `sha256:af2c19c8f457977011653519905408e861235272007daca50b92fc685f1aef73`,
  Codex CLI **0.153.4**. Grader/reference image:
  `sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`.
- New normal grades pin and record `grading_environment` separately from the
  agent image in metadata. Old missing grader evidence stays unknown. Regrade
  provenance takes precedence when displaying a regraded score.
- Apps and web are disabled for current launches. The initial 35 qualifying
  runs had apps available but no observed external invocation; their separate
  comparison cohort remains recorded. Do not relabel them as apps-disabled.
- Five quota attempts and one externally contaminated old Astra BibTeX Python
  attempt are excluded, with original artifacts preserved. The old Python UID
  is `951672ad-92f0-442d-87cf-6b4235a6418d`; the valid retry UID is
  `6f1f4ac5-698a-4e0e-a6cb-5d005a97bbdf`.
- Tool definition remains `underlying_tool_invocations_v2`. Preserve complete
  input/output/cache/reasoning counts. Reasoning is a subset of output, not an
  additional billable total. Ambiguous failed wrappers can make only the tool
  count unknown; do not substitute zero or drop authoritative token usage.
- `network_audit.py` recognizes one exact, source-proven relay-reset traceback
  and retains every raw byte/hash. It otherwise rejects malformed/unknown
  records and unexpected allowed destinations. Do not skip arbitrary non-JSON
  lines. Hosted-tool auditing remains separately required.
- The 43 qualifying runs at the pause have **$152.350269** in recorded
  API-equivalent estimates; the six excluded attempts total **$54.228829**.
  These are not subscription charges. The four in-flight runs were not yet in
  those sums; use the final snapshot for their recorded usage.

## Dashboard and publication checks

Both dashboards now default to the newest exact scoring version present in
the loaded dataset. Explicit older selections remain available; mixed selections
are labelled. Same major version does not establish comparable tests, and even
the same version does not independently prove identical input or test hashes.
The main dashboard still automatically selects only combinations with three
runs for every selected eval/language. Select one-run results manually. This
collection intentionally does not meet that default three-repeat threshold.

Earlier historical non-RS274 source artifacts were unavailable here, so those
results retain their historical scoring versions. Do not present them as
regraded or compare them to corrected scores without acknowledging the rubric
difference. Recover their original sources from the other workstation for a
future zero-inference migration, rather than silently relabelling versions.

After reviewed publication, refresh the report and dashboards sequentially:

```sh
sg docker -c '.venv/bin/python3 ../work/non-rs274-audit/write_checkpoint.py'
.venv/bin/python3 published_results/web/build_results_json.py
(ulimit -v 524288; .venv/bin/python3 published_results/web/build_test_results_json.py)
```

The last command adds a Linux 512 MiB process limit as a secondary guard; the
streaming writer normally uses much less. Validate a large per-test aggregate
with a streaming reader rather than `json.load` or `read_text` followed by
`json.loads`. The aggregate can exceed 1 GB even though its source run files are
small. Retain the old file until successful validation if comparing versions.

The per-test aggregate is intentionally ignored by Git. Check changed numeric
fields against actual publication records and preserve prior payload/audit
hash chains. The 43-row checkpoint verified all 1,776 baseline rows unchanged
except explicit provenance corrections. Full applicable harness validation was
359 tests plus six subtests; three host-Cargo cases were skipped and 23
Docker/model cases deselected. The final dashboard default patch passed syntax
checks and 31 independent functional assertions. Detailed local validation is
under `work/non-rs274-audit/`, including `dashboard-43-validation.json`,
`dashboard-exact-version-independent-review.json`, and each final regrade's
`promotion-validation.json`. No further broad tests are needed merely to resume.
