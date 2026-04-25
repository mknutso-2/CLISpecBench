# Changelog

## v1.2.0 — 2026-04-25

- Added a `superseded` VLR/EVLR kind covering the LASF_Spec record-id 7 marker
  the spec defines for negating an existing VLR/EVLR; the JSON surface
  round-trips its payload as `data_b64`, and the reference and harness handle
  inspect/render symmetrically. New inspect and render tests cover both the
  VLR and EVLR placements.
- Refactored validation tests so a single error-envelope regression no longer
  cascades. Most tests now assert only that the input was rejected via a
  permissive `_was_rejected` check; the exact `invalid_document` /
  `invalid_request` distinction is pinned by a small set of routing tests in
  `test_schema.py` (envelope-shape gates plus a malformed-base64 routing
  test).
- Reorganized the inspect header tests so format-invariant fields (identity,
  scale/offset, fixed-value fields like `header_size`) are parametrized by
  field on a single representative point format instead of running 11 times
  per format; format-varying fields (counters, layout offsets, extents) keep
  per-format coverage where the format genuinely changes the value.
- Split `test_inspect_point_format_record_blocks` into separate VLR and EVLR
  tests so VLR decoding bugs and EVLR placement bugs report independently.
- Tightened the base prompt to make "malformed standard LASF_Spec or
  LASF_Projection record" an `invalid_document`, removing the ambiguity that
  the spec line about Extra Bytes mismatch could be read as silently
  downgrading the bad record to opaque metadata.
- Reworded the waveform-absent serialization contract in
  `technical-requirements-prompt.md` to read as a JSON-to-bytes serialization
  rule (descriptor index 0 + zero waveform fields) rather than free-floating
  behavior, and explicitly narrowed the contract so intra-packet waveform
  layout (per-packet sample alignment and the spec's even-byte padding rule)
  and the ESRI WKT dialect are out of scope. Mirrored that scope note in the
  agent-facing base prompt and the LAS README.
- Added a "Reference language" section to the LAS README explaining why LAS
  intentionally ships only a Python reference.

## v1.1.0 — 2026-04-24

- Changed inspect behavior to preserve stored public-header fields and validate
  unambiguous modern counters, by-return counters, and coordinate extents
  against parsed point records instead of deriving replacement values.
- Added coverage for modern multi-return count tables, malformed public-header
  counters/extents, multiple EVLRs, external waveform references, and
  waveform-capable point formats with all-zero waveform blocks.
- Added render-side validation for decoded VLR/EVLR payload semantics, VLR
  scalar integer ranges, public-header scalar ranges, LAS ASCII text fields,
  strict base64 payload syntax, point field integer ranges, and coherent legacy
  point counter pairs.
- Tightened render numeric/text validation so oversized binary-float values and
  embedded NULs in LAS text fields report `invalid_request`, including Extra
  Bytes floating descriptor triplets.
- Added strict evaluator-side decoding for rendered LAS base64 and positive
  render coverage for GeoASCII VLR payloads with NUL-separated strings.
- Broadened Extra Bytes coverage across scalar, vector, signed, unsigned, and
  floating-point storage data types.
- Clarified the technical contract so inspect returns validated stored
  public-header fields while render recomputes layout-derived fields.

## v1.0.3 — 2026-04-24

- broadened the legacy-format render tests so they accept either spec-valid
  writer choice for legacy counters instead of pinning one compatibility policy
- removed a discrepancy test assertion that over-specified legacy by-return
  reconciliation beyond the LAS 1.4 corpus

## v1.0.2 — 2026-04-24

- fixed render-side semantic validation to report `invalid_request` for invalid
  render datasets instead of leaking `invalid_document`
- reconciled `legacy_number_of_points_by_return` in inspect output when point
  counts are derived from parsed points
- narrowed the point-format tests so header, point, VLR/EVLR, exact-render, and
  ambiguous legacy-waveform roundtrip checks fail more independently

## v1.0.1 — 2026-04-24

- corrected the inspect example in `technical-requirements-prompt.md` so its
  derived header fields match the included WKT VLR

## v1.0.0 — 2026-04-24

- introduced the LAS eval on `main`
- checked in the official LAS 1.4 PDF and a local layout-oriented text
  extraction in `prompt/docs/`
- defined a full LAS 1.4 inspect/render contract for point formats 0-10, VLRs,
  EVLRs, CRS records, waveform metadata, and extra-bytes metadata
- added a Python reference implementation and hidden pytest suite
