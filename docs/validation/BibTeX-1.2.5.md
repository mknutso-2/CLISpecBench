# BibTeX 1.2.5 validation — 2026-09-17

This private scoring repair follows the already supplied authority hierarchy.
All model-visible prompts and documents remain byte-identical. There are still
386 scored cases. No submitted implementation is edited.

## Authority and independent evidence

The supplied `bibtex.web` branches to `bst_done` at BST EOF (3478–3479), then
closes the BST and BBL files (3482–3483). `a_close` merely calls `close(f)`
(1098–1100); it cannot drain the separate logical `out_buf`. `write$` adds to
that buffer (11288–11300). Calls to `output_bbl_line` occur through wrapping
(7633) and `newline$` (10489), not at EOF.

Summary §3.6, lines 397–401, contradicts this by requiring pending content to
be flushed at exit. The base prompt (24–28) and summary introduction (29–33)
explicitly give the authoritative source precedence. This is an ordinary
summary error, without the explicit permission/exception language used for
no-op `top$` or name-spacing approximations. Capitalized MUST does not reverse
that hierarchy. The same reasoning already corrected adjacent mandatory
trailing-whitespace preservation in 1.2.3. The earlier validation claim that
both sources require EOF flushing was incorrect and has been corrected.
Changing public wording remains deferred; no new input contract is imposed.

An independent reviewer traced those paths and ran five separate-process
probes against the existing local BibTeX 0.99d (TeX Live 2023/Debian) oracle.
Executable SHA256:
`09d80947981f425cf7ca25d8a3bdb32df352fecd4eb00973771edf8598e6edd7`.
Supplied WEB SHA256:
`04c15be36dce19be38361617f139b1b8a70aa21f97def5cdc478622941398fa0`.
All probes exited 0 and matched exactly:

| Probe | BBL output |
| --- | --- |
| Short bare write | Empty |
| Flushed `seen` prefix, then pending text | `seen` and LF only |
| Short write followed by `newline$` | `hello` and LF |
| 70 `A`s, a space, then 20 `B`s; no final newline | 70 `A`s and LF only |
| Same wrapped text, followed by `newline$` | 70 `A`s, LF, two spaces, 20 `B`s, LF |

The compatible 0.99d executable and nonfunctional 0.99e source differences
have the provenance already described in the 1.2.3/1.2.4 notes. Exact probe
inputs, outputs, commands and hashes remain under local
`work/bibtex-eof-followup/oracle/`; the test itself needs no external oracle.

## Independence and regression controls

Semantic helpers now end observations with explicit `newline$`, including
writes inside branches and loops. Standalone name, entry-state, direct-output
and character fixtures do the same. The multi-entry state probe flushes once
after iteration, preserving its existing separators. Assertions and payloads
are unchanged; there are no new tolerance paths, skips or global output
rewrites. Canonical style parity fixtures are unchanged.

The old `test_bare_write_flushes_at_end_of_run` becomes
`test_pending_write_is_discarded_at_end_of_run`. It writes a flushed sentinel
before pending text and requires exactly the sentinel line. Producing no BBL
cannot earn credit. The C++ reference no longer performs an automatic EOF
flush. This is a reference correction, not a submission patch.

Under offline grader image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`:

- Corrected C++ reference: **386/386**.
- Unchanged 1.2.4 reference (EOF-flush mutant): **385/386**, failing only the
  dedicated EOF test. Its other 385 observations are unaffected.
- Sol Max JavaScript (`acd96c79-8fa0-402c-b3ee-875a25629538`): **383/386**,
  versus the original **314/386**. Exactly 69 false failures become passes;
  the remaining three failures concern the shared database/function namespace
  (two observations) and positive past-end name selection. Explicit flushing
  exposes the latter's incorrect empty name; its old empty BBL already failed.
  All eight independent canonical-style parity cases pass under both suites.

These outcomes show why 72 failed observations did not mean 72 separate bugs.
The repair preserves real defects and does not tune expectations to this run.
One early reference check exposed another unflushed loop fixture; it was fixed
before the final full reference/control checks. Original sources and result
bytes remain intact; programs execute only in disposable offline Docker copies,
one at a time. Ruff, strict Pyright and `git diff --check` pass. Independent
review of the private test/reference changes found no correctness or contract
blocker. Saved-source official regrades and their publication hash chains are
recorded separately after committing this scoring revision.
