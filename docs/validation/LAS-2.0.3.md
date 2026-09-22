# LAS 2.0.3 fixture refinement — 2026-09-12

> Later correction: [LAS 2.0.5](LAS-2.0.5.md) withdraws the interpretation
> that metadata/storage-free zero-waveform files must be accepted. Any
> classification below of those four failures as established model defects is
> superseded; the historical measurements themselves remain preserved.

The public inputs, all 223 case IDs, reference implementations and generated
submissions are unchanged. One negative render fixture now provides an explicit
one-byte `extra_bytes_b64` tail (`AQ==`) against its existing Type3 Extra Bytes
descriptor, which declares a two-byte unsigned short.

Previously that fixture omitted the tail. The public technical schema describes
exposing extra bytes and recomputing point-record length, but defines no render
default for an omitted tail. The saved Luna Max C++ submission inferred the
length from metadata and zero-filled the omitted tail. Requiring rejection of
that omission introduced an unstated rule. The explicit one-byte/two-byte
contradiction tests the intended metadata-versus-data invariant without choosing
an omission policy. A valid tail of exactly two bytes must not trigger this
negative assertion.

Pinned offline Docker validation used
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`,
with read-only repository/source mounts and disposable execution copies:

| Control | Result |
| --- | --- |
| Unchanged Python reference, full suite | 223/223 |
| Unchanged Luna Max C++ submission, full suite | 215/223 |
| The repaired negative, both programs | Correctly rejected |

Luna C++ previously scored 214/223 under 2.0.2. Its eight remaining failures are
four rejections of valid absent-waveform files and four missing waveform range
checks. Source and transcript review explain both clusters; neither is an
incomplete generation or grading run. Raw full reports are retained under this
workstation's `work/engineering-audit/LAS-2.0.3-*.json`. Ruff and strict Pyright
pass for the changed test.

The current suite hash is
`ae443df15b64e305925f2f1f3dbcfdcbbce47d71c5abaa80c538e9a288ddcc66`.
It supersedes 2.0.2 hash
`542e03956e2bb05d2a8f945764d82f51919a780d4631aa76f387eddb139163dc`
for current reporting. Original generation results and all earlier regrade
records remain historical evidence; promoting a corrected grade must retain
their identities, original scores, telemetry and provenance. No new model
inference is needed to evaluate this correction.
