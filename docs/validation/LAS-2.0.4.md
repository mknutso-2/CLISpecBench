# LAS 2.0.4 waveform-storage fixture correction — 2026-09-12

> Later correction: [LAS 2.0.5](LAS-2.0.5.md) withdraws the interpretation
> that metadata/storage-free zero-waveform files must be accepted. Any
> classification below of those four failures as established model defects is
> superseded; the historical measurements themselves remain preserved.

All model-visible input bytes, reference implementations and generated sources
are unchanged. The hidden suite still contains 223 cases. One negative fixture
now declares external waveform storage while retaining an internal waveform
packet EVLR, instead of requiring rejection solely because the deprecated
internal-storage bit is clear.

## Public-contract basis

The supplied `prompt/docs/17-030r1-layout.txt` preserves the LAS 1.4-R13 text:

- Table 4, lines 489–491, says that when global-encoding bit 1 is set the
  waveform packets are internal, and immediately calls this deprecated.
  It does not say a clear bit requires rejecting an otherwise located internal
  waveform record.
- Table 4, lines 492–495, says that setting bit 2 declares the waveform packets
  to be external in the corresponding `.wdp` file; it also makes bits 1 and 2
  mutually exclusive.
- Lines 613–617 independently define the public-header waveform offset as the
  location of the internal waveform EVLR header, with zero required when no
  waveform records are contained in the file.
- `prompt/base-prompt.md`, lines 20–25, requires errors for standard metadata
  that contradicts the rest of the file.

The former fixture cleared bit 1 but retained a consistent internal EVLR,
header offset, descriptor and packet interval. Requiring its rejection selected
an interpretation that the public corpus does not unambiguously require. The
new fixture also sets bit 2, explicitly contradicting the internal packet data.
Bit 1 remains clear so this case does not merely repeat the separate
mutually-exclusive-bits rejection.

Acceptance or rejection solely because deprecated bit 1 is clear remains
unscored. This correction does not require reference implementations to adopt
either interpretation, and makes no change to the public contract. The
reference still takes the stricter interpretation; that is not used as evidence
that the former negative was justified.

## Validation and provenance

Validation uses offline Docker image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`,
with the repository mounted read-only, fresh disposable source copies and a
maximum of two concurrent graders. Every original source-file manifest and
original result file is checked unchanged afterward. Ruff, Ruff formatting and
strict Pyright pass for the modified test.

The candidate changes the suite hash from
`ae443df15b64e305925f2f1f3dbcfdcbbce47d71c5abaa80c538e9a288ddcc66`
to `d280a8b50945a5e93f598b2f9d82055b6e4437b1a0ab5df2feac595070e3602b`.
The renamed case is explicitly paired in each comparison; all 222 remaining
node IDs must match the previous suite exactly. Comparison records preserve
every old/new failed node, including unchanged failures, rather than relying on
aggregate-score differences alone.

All results below are out of 223. Prior counts are the preserved 2.0.3
regrades for the eight original C++/Python submissions, and the original 2.0.3
reports for the two new Astra JavaScript/Rust submissions.

| Implementation | 2.0.3 | 2.0.4 candidate |
| --- | ---: | ---: |
| Python reference | 223 | 223 |
| Astra Max C++ | 223 | 223 |
| Astra Max Python | 223 | 223 |
| Astra Max JavaScript | 223 | 223 |
| Astra Max Rust | 222 | 223 |
| Sol Max C++ | 219 | 219 |
| Sol Max Python | 219 | 219 |
| Terra Max C++ | 218 | 218 |
| Terra Max Python | 223 | 223 |
| Luna Max C++ | 215 | 215 |
| Luna Max Python | 216 | 216 |

Across all ten submissions, every one of the 222 unchanged nodes has exactly
the same outcome as before. Nine submissions pass both the old and replacement
negative. Astra Rust is the only score change: its deliberate deprecated-bit
interpretation failed the old assertion, but it correctly rejects the new
external-versus-internal contradiction. No newly exposed failures occurred.

The remaining failures are unchanged: Sol C++/Python each reject four valid
zero-descriptor waveform files; Terra C++ has those four failures plus an
undocumented Extra Bytes descriptor decoding failure; Luna C++ has four
zero-waveform and four packet-interval failures; Luna Python has four
zero-waveform failures, two header-overlap failures, and one Extra Bytes
floating-triplet overflow failure. Every exact node ID and outcome remains in
the comparison records.

A disposable mutation control removed only Astra Rust's explicit rejection of
internal packet data with the external-storage flag. It scored 222/223 and
failed only the new negative; all other 222 cases, including mutually exclusive
flags and positive waveform behavior, still passed. The unmodified Rust source
scored 223/223. This shows that the replacement observes its named condition
without adding a shared prerequisite to unrelated tests.

The workstation evidence is under `work/las-deprecated-bit-followup/`:
`validation-manifest.json`, `candidate-hashes.json`, `comparison-summary.json`,
per-run `reports/*.comparison.json` and full pytest reports, plus
`mutation-control.json`. The drivers use fresh execution copies and preserve
original result/source hashes. Official promotion should retain the old score,
run UID, telemetry and generation provenance in a separate regrade record.
