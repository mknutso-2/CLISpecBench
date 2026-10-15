# Collection controller stabilization

Status: preparatory software, not a running Sonnet collection. Matthew approved
continuing the October 10 Haiku retrospective recommendations. The existing
heartbeat remains paused. No new model scope, retry authority, credential,
lease, backend service, publication, or paid overflow is inferred.

## Implemented building blocks

`clispecbench.collection.evidence` stores content-addressed, hash-verified raw
bytes. `save_review` accepts exact already-assembled UTF-8 bytes, their expected
digest, and the collection's strict validator. It creates the final atomically
without overwriting existing evidence, checks saved bytes, and validates again.
No terminal transport, JSON float conversion, signature generation, or timestamp
change is needed. A different existing final fails closed. These functions do
not replace substantive review or authenticate a reviewer.

`Journal` uses immutable sequential event files with a previous-event hash and
artifact reference. Interrupted temporary files are not events. A stale head,
sequence gap, altered object, conflicting append, or duplicate JSON key fails
closed. The caller must hold the collection's ORIGINAL shared dispatch lock;
there is no second lease, scheduler, dispatch lock, or automatic model retry.
The journal carries fixed event codes and hashes, not raw exception messages or
credentials. Filesystem atomic hard-link support is required; unsupported storage
fails closed rather than falling back to an overwrite.

Retain the expected journal head outside the event directory when resuming.
A hash chain alone cannot detect deletion of its final record if no expected
head survives. The journal is an integrity check, not filesystem immutability
or a signed reviewer attestation. A failed post-save validation preserves the
candidate bytes for diagnosis; it does not authorize counting or releasing it.

`clispecbench.collection.readiness` separates dispatch from finalization:

- Dispatch needs an authorized, never-reserved target and fewer than eight held
  slots, plus all frozen/ownership/lease/resource/quota/authentication checks.
- Finalization needs its own completed/graded, assigned-reviewed, independently
  peer-checked, deterministic-valid, same-model record and actual own generator,
  grader, proxy, and wrapper drain. Other authorized workers may still run.
- An exhausted queue or eight held slots never prevents release of that reviewed
  own record. PAUSED/STOPPED still block both paths; no error or pause bypass.
- Freshness is measured at the actual current decision time, including rejection
  of future timestamps. Usage and operational observations must be <=120 seconds
  old. Expensive validation precedes the late ordinary-usage read; integrations
  must finish with fresh actual ownership as well, never reuse stale snapshots.
- Ordinary five-hour/weekly utilization remains <=70%, extra usage confirmed off,
  valid reset window (null only at reported five-hour zero), and authentication
  >=30 minutes. A future integration may tighten, never reduce, this runway.

These are pure advisory primitives, not integrated launchers. A next-model
integration must bind exact observations/assignments/signatures, use the original
lock, verify pinned inputs, images and invocation, and pass replay tests before
dispatch. Do not replace historical Haiku guards/manifests or rewrite its reviews.
No immutable-evidence validation cache has been introduced.

The private Haiku dashboard's saved-evidence mapper now excludes explicit
unscored/operator/mixed omissions from valid matrix reviews, validates the exact
authorized final ICal replacement, and maps that attempt instead of its omitted
original. An offline read of the actual receipts reports 96 valid reviewed cells
and 11 omissions, with final ICal C++ max score 459/467 and unknown whole-run
dollars. The running server was NOT restarted or reloaded in this preparation;
this is a tested code correction, not a claim about the live page.

## Proposed single operating-policy approval

This section is a proposal, not an authorization receipt. Before Sonnet launches,
record one human-approved finite policy with the following fields resolved:

1. Exact model/version, matrix (96 cells or RS274 only), compatible prior-result
   reuse rules, input/image/CLI/network/limits pins, and publication scope (default
   private, no commit/push). Sonnet does not imply authority to start Opus.
2. Preauthorized controller-only operations: local private snapshots, append-only
   receipt reconciliation, tested byte-preserving serializer/parser repairs and
   same private dashboard recovery. Preserve all originals and test every repair;
   record the exact affected artifacts and operational version once, not recursive
   historical-final aliases. Scientific inputs remain immutable and separate from
   independently versioned controller code.
3. Optional bounded infrastructure replacement policy: at most one fresh attempt
   per affected cell, at most eight across the finite matrix; only independently
   evidenced local infrastructure interruptions after full omission review. No
   retries of replacements. Unknown failures, provider/auth errors, model errors,
   and cross-model evidence require disposition unless separately covered by the
   approved policy. Never resume an interrupted original or hide its usage.
4. Evidence policy: pinned CLI notice grammar, native-versus-stream provenance,
   reported aggregate token labels, and unknown whole-run dollar accounting.
   Collect ALL blockers in one diagnostic before asking a coherent question.
   Do not insert records into raw streams or synthesize final counters. Unknown
   records, conflicting identities, missing substantive evidence, and actual
   different models remain holds, not generic waiver cases.
5. Recovery limits: only one exact collection-scoped lifetime owner, same approved
   backend and private dashboard, exact PID/birth/command verification, original
   shared-lock ownership, and preserved interruption evidence. If owner identity
   is unknown, fail closed. No service installation/reconfiguration, broad process
   kills, cleanup, duplicate leases, networking changes, or auth refresh by default.
6. Fresh ordinary usage before every refill and operational finalization. Start one
   Sonnet cell, measure same-window account-wide use, then choose concurrency;
   eight is a ceiling. Wait for quota reset without a new permission request.
   Never enable extra usage, purchase credits, redeem resets, or attribute
   parallel account deltas to a single run.
7. Designated same-model substantive reviewers from the start; independent peers
   cover named exceptions, deterministic validation checks signatures/coverage,
   coordinator handles fresh operational gates. No second routine full rereview.
8. A single dashboard approval is an instruction for its exact current proposal;
   no routine repeat-in-chat request. Keep fingerprint/schema/peer/Host/Origin/CSRF
   checks. Custom text is intent, not executable code or a safety-gate bypass.

## Authentication and backend readiness before activation

The supported `claude setup-token` subscription OAuth option merits evaluation
with the PINNED CLI, credential mounting, web-enabled condition, and ordinary
usage checker. It is not implemented here. The current ordinary usage checker
reads the Windows login credential; a long-lived model token alone cannot make
that checker fresh or extend its separate credential's lifetime. Preserve both
auth-source identities and verify account consistency without exposing tokens.
Do not put a token literal into arguments, prompts, logs, journals, Git, or
environment dumps. Do not substitute API billing for subscription collection.

Choose a backend/controller lifetime independent of desktop app updates before
another unattended window. This requires an explicitly approved host lifecycle
mechanism, not another hidden lease started during preparation. No service or
scheduled task has been installed. Test recovery without model calls and require
ample physical disk headroom before starting, not merely the minimum disk floor.

## Activation checklist

- Pure fault replays pass (including ceiling/final-cell, started receipt loss,
  stale/future usage, revoked auth, lost backend, Unicode/large review bodies,
  duplicate event and tampered evidence). Ruff and strict Pyright pass.
- Live dispatch integration, pinned-parser replay and lifecycle recovery are
  separately verified without submitted-code execution on the host.
- Exact finite scope and bounded operating policy are confirmed once; current
  paused automation is updated, not duplicated. No automatic Sonnet/Opus start.
- Confirm exact model/account/reasoning availability and compatible historical
  attempts before any necessary isolated smoke. Never duplicate a valid smoke.
- Dashboard distinguishes valid scored results, omissions, accounting uncertainty,
  routine review work, and actual user-action issues. Saved labels are not live
  worker ownership proof; use plain-language states.

## Preparation validation

- Controller fault-replay suite: 50 tests passed; no model, Docker, account or
  submitted-code calls.
- Dashboard mapper/security suites: 58 tests passed; frontend mock suite: 60
  assertions passed. Tests use temporary fixtures, not the live approval channel.
- Explicit Ruff and strict Pyright checks passed for all changed Python files.
- Offline actual saved-receipt mapping: 96 valid reviews, 11 omissions, zero held;
  exact final replacement UID and 459/467 selected. Stale saved usage remains a
  warning, never dispatch authority.
- Seven historical guard/helper/manifest byte hashes match the closing Haiku
  checkpoint. No historical review, raw benchmark evidence or frozen guard was
  migrated by these changes.
- Broader non-Docker/non-agent harness run: 565 passed, three failed, 26 deselected,
  58 subtests passed. Failures are in untouched CMake executable discovery,
  Codex invalid-UTF-8 tool-count handling, and Windows symlink privilege setup.
  They are recorded, not silently waived or fixed by this preparation. The broader
  run collected the controller suite before its final seven additional tests;
  the final 50-test suite was then run separately.

Launcher integration, pinned evidence-parser replay, independent host lifecycle,
authentication compatibility and exact Sonnet scope/policy still require the
activation work above. These test results do not authorize collection.

Official authentication reference:
https://code.claude.com/docs/en/authentication
