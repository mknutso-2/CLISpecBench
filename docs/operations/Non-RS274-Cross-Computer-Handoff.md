# Continue the non-RS274 collection on another computer

## Windows continuation — October 1 evening

**October 2 user decision:** document the [ICal raw-projection issue for a future
fix](../validation/non-rs274-2026-09-12/ical-valarm-publication-hold.md), retain frozen
scores with explicit caveats, and continue collection. The earlier VALARM hold is
resolved; do not pause again solely for this known ambiguity. No prompt, test,
scoring policy or raw evidence was changed. ICal cpp/js/rs completed at456/467,
447/467 and454/467; IGES cpp at244/249. All four have independent reviews. Their
local publication is phase-gated in the queue ledgers; check finalization markers
and machine-readable counts before dispatch. Sol IGES Python still needs artifact
transfer and must never be regenerated.

The four Sol Max MARC21 languages completed and were independently reviewed on
the Windows workstation: cpp 2876/2900, py 2896/2900, js 2848/2900, rs 2900/2900.
Terra Max BibTeX cpp/js/rs and GEDCOM cpp/js/rs also completed and were independently
reviewed: 362/386, 372/386, 382/386, 169/212, 118/212, and 128/212 respectively.
After the latest publication checkpoint: **111 reviewed/published cells**
(Astra28, Sol27, Terra28, Luna28). All39 authorized Windows generations are
reviewed/published; only completed Sol IGES Python awaits artifact transfer/review.
No evaluation worker remains active. This checkpoint includes the canonical
publications, portable reviews and main dashboard index. Exact live counts and
publication-stage markers remain authoritative during an interrupted update.

The user now authorizes **four concurrent generation slots**, superseding the
serial-only instructions below. Each completed run must be reviewed before its
slot is refilled. The Windows queue/ownership records are under the ignored
`automation_logs/non-rs274-oct1/`; one same-chat heartbeat manages continuation.
At October 2 14:05 Chicago, all Luna BibTeX languages are reviewed/published:
cpp368/386,js370/386,py355/386,rs365/386. Luna GEDCOM C++ is published at164/212,
with shared-fixture and VOID JSON-representation caveats recorded in its review.
All Luna GEDCOM languages are now reviewed/published: cpp164/212, js202/212,
py201/212 and rs165/212. Rust's47 failures include correlated SNOTE/EVEN
rejections and missing datatype validation; its passing render-datatype negative
is masked by a shared-fixture rejection, documented for a future revision.
Luna ICal C++ is reviewed/published at450/467: seven groups explain17 failures,
with no known raw-projection ambiguity affecting them. Exact242tools recovered
from session evidence; canonical cost$1.129900 retained with one compaction caveat.
Luna ICal Python456/467 and Rust442/467 are now reviewed/published. Python's11
observations are gap3/iTIP5/orphan3; Rust retains11 raw-duplication caveats and
one invalid floating STANDARD UNTIL fixture, documented for a later revision.
Their exact310/286tools and canonical costs reconcile with session evidence;
one compaction each is separately documented. No frozen score changed.
ICal JavaScript is reviewed/published at457/467, with all ten failures mapped to
implementation defects. Raw432 tools and canonical$1.912947 reconcile; three
compactions and a post-completion cleanup logging anomaly are documented in its
portable review. Luna IGES JavaScript is reviewed/published at243/249: six
observations map to query wrapping3,0H1,trailing DDF1,input EOF newline1.
Raw313 tools and canonical$1.524918 reconcile; four compactions are documented.
IGES Python245/249 and MARC21 C++2877/2900 are now reviewed/published;
Python229tools were recovered from session evidence, with one compaction
disclosed. MARC21 raw104tools reconcile without correction. IGES C++231/249
is now independently reviewed/published with explicit AVDT-mapping and
first-physical-line writer-test caveats. Raw377tools/$1.599920 reconcile;
five compactions are disclosed. IGES Rust239/249 is now reviewed/published with
five genuine observations and five known mapping/writer-test caveats. Its GitHub
source-fetch attempt was explicitly blocked with403 and returned no content;
307tools recovered publication-only, three compactions separately documented.
MARC21 JavaScript2838/2900 and Python2884/2900 are reviewed/published; missing008
checks and lossy rule extraction explain their failures. Tools99/61 reconcile.
Luna MARC21 Rust2887/2900 is now reviewed/published. Its13 observations map to
007 optional-length restrictions4, forbidden category fill1, missing008 checks4
and omitted018$a4. Publication-only82tools and canonical$0.439627 reconcile,
with no compaction. Both dashboards are verified at1887runs/1,215,735outcomes.
No generation cell remains outstanding. Last checked ordinary usage showed3%used;
no reset credit was redeemed by this collection.
The earlier BibTeX Python's shared name-scanner bounds bug
explains ten failed observations. A recovered proxy-connection reset did not
terminate its generation; full diagnostics and independent reviews are retained.
The completed ICal Python retry preserves its earlier excluded quota attempt.
Terra MARC21 JS/Rust are reviewed/published at
2848/2900 and 2857/2900, with exact session-backed tools83/73. Terra MARC21 cpp
is reviewed/published at 2876/2900; IGES js/py/rs at 228/249, 247/249, 248/249.
The IGES JS score has [fixture/contract caveats documented for a future revision](../validation/non-rs274-2026-09-12/iges-frozen-suite-followup.md),
not silently repaired or rescored. Local Python reference passed 249/249.
Consult ledgers for current state; all39 Windows launch ledgers have finalized
reviews. Sol IGES Python remains transfer-only and must not be regenerated.
The same-chat heartbeat is PAUSED after collection completion. Docker has no
remaining evaluation/proxy containers. The existing hidden WSL keepalive remains;
no daemon/image/network settings were changed during finalization.
Check actual ledgers/process state;
do not launch from another computer without coordinating ownership.

CLI remains 0.153.4. The local agent image is
`sha256:e7784a9f63c319fe9b86b591402f5991fdb15814a42db3d87d2050408a65c5c7` and grader
is `sha256:922c3bc7435e5546e737bf77b5bc8c07d15f86c9bad7f6fc68555cf8fbf04dc5`;
these differ from the source-machine images below. Frozen hashes match; isolation
and toolchain checks pass; local references pass MARC21 2900/2900, BibTeX 386/386,
GEDCOM 212/212, ICal 467/467, and IGES 249/249. Valid UTF-8 telemetry initially failed implicit Windows cp1252
decoding. Preserved-evidence reparses recover exact tool totals without changing
tokens, costs, scores or raw artifacts; portable audits are linked from each new
publication. Future local wrappers use `PYTHONUTF8=1`. This is a host decoding
setting, not a model-input or grading change.

## Original source-machine handoff

Snapshot: **October 1, 2026**, after local commit `954de39` and integration of
remote `347fbab`. Read this document before older resume notes. The user
requested committing/pushing the current state for a possible handoff.

## If the source machine cannot push

The initial HTTPS push failed because this workstation has no GitHub Git
credentials configured. Local commits are preserved. A verified Git bundle is
available beside the repository at
`outputs/clispecbench-handoff-2026-10-01.bundle` (relative to the workspace
parent). It carries the exact local commits, including their original hashes,
and requires upstream history through `347fbab`. Unlike a patch or recreated
commit, it preserves the commit IDs referenced by validation records.

If the push has not subsequently succeeded, a plain pull will still miss this
work. Transfer that Git bundle and the separate Python artifact archive to an
authenticated computer. In its clean CLISpecBench checkout, after fetching the
remote, import the bundle and fast-forward before pushing:

```bash
git fetch origin
git bundle verify /path/to/clispecbench-handoff-2026-10-01.bundle
git fetch /path/to/clispecbench-handoff-2026-10-01.bundle main:handoff-oct1
git merge --ff-only handoff-oct1
git push origin main
```

If fast-forward fails because the receiving machine has additional commits,
review and merge those changes normally; do not reset or force-push. If the
original machine authenticates and pushes successfully first, the bundle is
unnecessary and a normal pull is sufficient for tracked files.

## What is done and what remains

The target is **112 cells**: seven tasks × four languages × four models,
**one qualifying Max run per cell**. Tasks: BibTeX, GEDCOM, ICal, IGES, LAS,
MARC21, WordCount. Languages: cpp, py, js, rs. Models: `gpt-6-astra`,
`gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`. RS274, other reasoning efforts,
and filling three repeats per cell are outside this collection.

**72 cells are reviewed and published** (Astra 28, Sol 23, Terra 12, Luna 9).
**40 remain: 36 new cells, three excluded cells needing fresh retries, and
one completed submission needing review.** The precise task/model/effort,
version, prompt hash and next action for every unfinished cell are in
[remaining-coverage.json](../validation/non-rs274-2026-09-12/remaining-coverage.json).
Use that file, not a guess based on the dashboard's default selections.

- [Completed results](../validation/non-rs274-2026-09-12/completed-results.json)
  bind all 72 reviewed cells to publication paths, raw hashes and accounting.
- [Coverage table](../validation/non-rs274-2026-09-12/README.md) is human-readable.
- [Excluded attempts](../validation/non-rs274-2026-09-12/excluded-attempts.json)
  preserves seven historical failed attempts; not all seven still need retries.
- [Public-input baseline](../validation/non-rs274-2026-09-12/public-inputs.json)
  records the frozen 28 task/language prompt hashes and current suite hashes.

The next **new** generation should be Sol Max `marc21-cpp`, then its other
three MARC21 languages. Finish the held IGES Python review first when its
artifacts are available. Then work through missing Terra/Luna cells in the
machine-readable list. Never regenerate an already qualifying published cell.

## One completed Python run needs its local artifacts

Sol Max `iges-py` completed normally at **244/249 under IGES 1.0.21** on
October 1 at 07:25 Chicago time. UID:
`672af3d3-3583-4bc6-a64b-882d79626ef4`. It has **not been reviewed or published**;
the provisional score must not be counted as a reviewed result yet.
The previously excluded UID `6cb7068d-e782-49c6-b8e2-1ab6ea5c2bbb` is separate
and remains excluded. Do not repeat this completed retry merely because a
fresh clone lacks the local raw files.

[Pending review record](../validation/non-rs274-2026-09-12/pending-python-review.json)
contains raw summary/accounting, original hash, launch identity, a per-file
manifest, and the transfer-bundle checksum. The approximately 1.1 MB archive is
on the original machine at:

```text
/home/matthew/Documents/Codex/2026-09-05/ca/outputs/non-rs274-handoff-2026-10-01.tar.gz
```

Its SHA-256 is
`0498f1e412941f9f1e623eb4b32e9d4254641498e0a004d7f29053cd180276e8`.
It contains only that run's raw result/report/source/events/session/network
artifacts and small launch/log/manifest records. It excludes host authentication
files, Docker images and the large generated dashboards. Transfer it separately;
**it is not in Git**. Verify its checksum and inspect archive paths, then unpack
into a staging directory. The archive's `CLISpecBench/transient_results/...`
subtree can be copied into the receiving clone; `work/...` contains launch
context, not portable runnable infrastructure. Absolute paths in logs/manifests
are historical and must be resolved to the receiving checkout without rewriting
original evidence bytes. Review generated source as data; execute it only in Docker.

If the archive cannot yet be transferred, the other 39 cells remain clearly
identified and runnable once machine ownership/setup is established. Leave
Python awaiting review and complete it when the artifact arrives. A Git pull
alone cannot finish its source/transcript review.

## What a pull does and does not transfer

Tracked: harness, tasks, frozen prompts, tests/references, skills, reviewed
publication JSON, portable regrade audits, checkpoint/validation documentation,
and the small main dashboard aggregate. The three remote README/figure/ignore
updates have been merged; do not discard them.

Not tracked: `transient_results/`, generated per-test dashboard, local Docker
images/caches, credentials, or the sibling `work/non-rs274-audit/` helpers and
run ledgers. Most earlier raw sources/sessions also remain on the original
machine. The current clone can run new cells without those earlier raw artifacts;
do not attempt historical regrades without transferring their source evidence.
Do not run the historical `write_checkpoint.py` on a new machine expecting it
to rediscover all 72 runs: it depends on those local artifacts. Preserve existing
checkpoint rows and append/update only verified new results and pending states.

## Setup and equivalent execution conditions

Read `AGENTS.md`, `.codex/skills/run-eval/SKILL.md`, and
`.codex/skills/author-eval/SKILL.md`; follow the native-Linux/Windows setup in
[README](../../README.md) and [agent run notes](Agent-Run-Notes.md).
Use `uv sync --locked`, a working Docker daemon and the receiving machine's
own Codex authentication. Do not copy or commit authentication files.

The established collection uses Codex CLI **0.153.4** and these image identities:

- Agent: `sha256:af2c19c8f457977011653519905408e861235272007daca50b92fc685f1aef73`
- Grader: `sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`

Images do not travel through Git. To reproduce them exactly, export/import the
existing images with Docker save/load and verify IDs, restoring the harness tags
`clispecbench-codex-cli` and `clispecbench-base`. Rebuilding the committed
Dockerfiles may yield different IDs. If rebuilding is necessary, verify toolchain
and reference behavior, record actual identities and keep the cross-image
comparison limitation explicit; never label a rebuilt image as the old one.
The current harness records agent and grader identities separately.

Before spending usage, run `uv run clispecbench hash --task marc21-cpp` (or the
chosen task) and compare with the tracked public-input/suite baseline. Confirm
Codex invocation disables hosted apps **and** web search, and metadata/network
evidence uses the `api-only` condition. The current adapter supplies these flags.
Check fresh ordinary account usage. No purchase or reset-credit redemption is
authorized. No recurring automation was created on the original workstation.

## Sequential execution and review

Establish one active owner across computers before launching. At this snapshot
no worker is active, and this handoff starts no further run. Recheck with the
original workstation/user if time has elapsed; local lock files cannot coordinate
two computers. The instruction remains **one submission at a time**, including
review/publication/checkpoint before the next generation. A local serial gate
is not a request to wait for a new user prompt after every run.

The tracked CLI can run the next cell without the old helper scripts:

```bash
uv run clispecbench run --task marc21-cpp --agent codex-cli --model gpt-5.6-sol --effort max --runs 1
```

Run it in a supervised persistent terminal, or use the receiving host's supported
detached launcher and retain its log/PID. Do not impose a short timeout. Check
that it actually starts model work. Retain every result/source/transcript/session
and record run UID, actual invocation/images and hashes. A fresh clone may start
again at `eval1/run1`; use UID plus task/model identity, never the directory number
alone, to distinguish retries from older excluded attempts.

After each generation:

1. Inspect original result, full transcript/session and generated source; confirm
   voluntary completion versus quota/infrastructure interruption. Review each
   failed case against the public contract and fixture prerequisites, grouping
   correlated observations rather than calling them independent defects.
2. Obtain independent correctness review, as requested by the user. Verify final
   completion claims, raw pytest outcomes and source identity. Preserve original
   evidence. Do not run submitted code on the host.
3. Verify input/cache/output/reasoning accounting against the session; reasoning
   is a subset of output. Recompute estimates using recorded rates. The existing
   tool definition includes commands and file changes; rejected nested actions
   require session evidence. Keep exact count unavailable when evidence cannot
   establish it. Do not discard correct token/cost data because tool count is null.
4. Publish only approved, qualifying results using the tracked publish command
   and a substantive editorial summary/notes. Preserve the `api-only` cohort and
   apps-disabled evidence. Do not publish account-quota/network/operator failures;
   record their excluded identity and preserve them for a fresh retry.
5. Rebuild the main dashboard **before** the per-test dashboard (the latter reads
   the former). `uv run clispecbench rebuild-dashboard` does this sequentially.
   On memory-constrained Linux, run report generation under `ulimit -v 524288`.
   Preserve the old aggregates first; stream the large comparison rather than
   loading it wholesale. Verify all previous rows and all new score/accounting/
   provenance fields. Keep the large per-test aggregate out of Git.
6. Update completed/remaining/excluded records and the coverage table. Preserve
   historical rows and estimates, and do not count an active or unreviewed run as
   completed. Commit the reviewed result/checkpoint, then proceed to the next cell
   while ordinary usage remains available and the user has not asked to stop.

All 28 model inputs stay frozen. Any necessary hidden-test repair must follow
repo comments/version/changelog/design requirements and independent review,
with saved-source regrades, preserved original grades and unchanged-input proof.
Public wording cleanup is a separate later revision; see
[deferred clarifications](../validation/non-rs274-2026-09-12/public-clarifications.md).
Do not silently rebuild/regrade old results just to simplify the handoff.
