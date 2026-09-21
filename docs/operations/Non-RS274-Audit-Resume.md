# Resume the non-RS274 audit and GPT collection

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

Coverage is **58/112**, with 54 cells needing qualifying results: Sol 16, Terra 17
and Luna 21. There are 48 unstarted cells and six retries (five quota, one provider
capacity); no earlier completed-review backlog. All 28 Astra cells are complete.
Collection covers all seven non-RS274 tasks, including their tests-only repairs;
the public-input revision remains deferred. The next selected pending cell is
**Terra Max / LAS Rust**. Inspect its live ledger before dispatch. Finish each
result's transcript, source, scoring and accounting review, then publish/commit
before the next run. The previous four-worker queue remains disabled. Seven
excluded attempts total **$54.862522**; qualifying estimates total **$271.341668**.
These are API-equivalent estimates, not subscription bills.

## Latest checkpoint — September 17, 2026

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

Final scoring versions: WordCount **1.0.4**, LAS **2.0.4**, GEDCOM **4.0.3**,
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
