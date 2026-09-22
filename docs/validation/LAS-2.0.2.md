# LAS 2.0.2 follow-up validation — 2026-09-12

> Later correction: [LAS 2.0.5](LAS-2.0.5.md) withdraws the interpretation
> that metadata/storage-free zero-waveform files must be accepted. Any
> classification below of those four failures as established model defects is
> superseded; the historical measurements themselves remain preserved.

All model-visible inputs are unchanged. Reviewing the first fresh Astra Max
Python submission exposed defects that the initial reference-only LAS audit
missed. The saved program passed 182/219 under 2.0.1; all 37 failures came from
an invalid shared input or an unspecified JSON representation requirement.
This follow-up repairs those tests and adds four missing interval checks.

## Waveform input validity and missing rejection coverage

The supplied `17-030r1-layout.txt` describes the Point Format 4 waveform offset
at lines 981–990: it is relative to the beginning of the Waveform Packet Data
header. The EVLR header is 60 bytes (line 1352); waveform bytes follow that
header internally or externally (lines 1767–1775).

The shared fixture supplied offset 2 and packet size 4. Its EVLR payload has
four bytes, so the packet starts at offset 60 and ends at offset 64. A correct
implementation rejected the old pointer into the header, causing 30 unrelated
inspection/render failures. The fixture now uses 60, with all packet bytes,
descriptor fields and other point values unchanged.

Four new checks independently exercise inspect and render with a header-overlap
range (offset 2, size 4) and a range extending beyond the payload (offset 60,
size 5). The reference now rejects both. These checks concern references to
stored bytes; they do not impose per-packet sample layout or padding validation,
which the public base prompt explicitly excludes. External payload length
cannot be validated without that external file; only its documented header
origin is constrained.

## JSON representation choices

The WKT fixture builder also leaked its private `_evlr_hint` marker into render
requests. The public contract defines no unknown-field policy, so rejecting
that field is permitted. Render requests now remove just that marker from
VLR/EVLR records. Other keys, missing fields, malformed values, record ordering
and the original dataset remain unchanged. A saved Sol submission rejected
ten positive render cases because of this leak.

- The public GeoASCII schema names only `text`. It does not say whether JSON
  retains the final binary NUL. Inspect permits the exact fixture string or
  removal of exactly one terminal NUL. Render permits the exact expected bytes
  or one extra terminal NUL introduced by the other convention. Embedded
  separators, all content, and GeoKey value offsets remain exact; broad
  whitespace/NUL stripping is not used.
- LAS classification lookup storage has 256 entries. The JSON contract allows
  omitted classes to mean empty descriptions on render, without requiring a
  sparse inspect result. Comparisons accept sparse or complete empty entries,
  while rejecting duplicates, invalid class numbers and incorrect descriptions.
- A binary descriptor index of zero means no waveform. The public optional
  object rule specifies serialization, not a unique inspect representation.
  The four zero-waveform cases accept omission or a complete seven-field zero
  object, require a nonempty observed point list of the correct length, and
  leave unrelated point/header/schema observations to their dedicated tests.

## Validation

Pinned, offline Docker image:
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`.
The repository and original submission are mounted read-only; execution uses
disposable source copies.

| Control | Result |
|---|---|
| Corrected Python reference / full suite | 223/223 |
| Unchanged Astra Max Python source / full suite | 223/223 |
| Unchanged Sol Max Python source / full suite | 219/223; four real absent-waveform validation failures remain |
| Unchanged Terra Max Python source / full suite | 223/223 |
| Unchanged Terra Max C++ source / full suite | 218/223; four absent-waveform failures and one overstrict Extra Bytes descriptor check remain |
| Original reference / four new range checks | 0/4 |
| Astra source with just the waveform fixture fix and new range checks | 216/223; seven representation mismatches remain |
| Astra source / seven repaired representation cases | 7/7, previously 0/7 |
| Narrow good/bad representation probes | 21/21 expected decisions |

Ruff and strict Pyright pass for the changed tests and reference. Representation
probes include missing data, wrong descriptions, duplicate class entries,
damaged strings, excess terminators and invalid zero-waveform objects. A second
reviewer checked the supplied public requirements independently.

Raw diagnostics and copies are retained in `work/las-followup/`. The initial
host diagnostic created five Python cache files beside the saved source; these
were identified against the pre-diagnostic source inventory and removed, with
the cleanup and authored-file hashes recorded in the run's review directory.
Subsequent controls use disposable copies. No authored submission file or
original result/test report was changed by the test repair.

The original 2.0.1 result remains a generation/grading observation. Publication
of a later grade must preserve its generation metadata, token usage and original
score, with a separate regrade record for the corrected rubric. A perfect score
is not proof of exhaustive LAS coverage or statistical independence: basic file
decoding remains a prerequisite of many observations.
