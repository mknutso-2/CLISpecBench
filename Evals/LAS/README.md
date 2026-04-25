# LAS

`LAS` asks the coding agent to implement a validator, inspector, and renderer
for ASPRS/OGC LAS 1.4 point cloud files using the complete checked-in official
specification corpus in `prompt/docs/`.

The submitted program must:

- inspect a base64-encoded LAS 1.4 file and produce a structured JSON dataset
  describing the public header block, VLRs, EVLRs, point records, CRS records,
  waveform metadata, and extra-bytes metadata
- render a LAS 1.4 binary from that dataset
- validate the input against the official LAS 1.4 specification, including
  point-format rules, unambiguous public-header fields and extents, CRS
  representation rules, VLR/EVLR structure, waveform rules, and extra-bytes
  semantics

The prompt corpus uses the official OGC LAS 1.4 PDF plus a local text
extraction of the same document. The PDF is authoritative.

## Why this is a good eval

LAS 1.4 is a strong CLISpecBench task because the specification is dense,
binary, and full of interacting invariants:

- 11 point formats with materially different layouts
- legacy-versus-1.4 compatibility rules
- bit-packed fields with distinct semantics for point formats 0-5 versus 6-10
- structured VLR and EVLR records
- required CRS behavior tied to the WKT global-encoding bit and point format
- waveform packet rules and EVLR placement
- typed extra-bytes descriptors with upcasting, flag bits, and mismatch rules

The task remains grounded in a single official domain specification rather than
an evaluator-authored subset.

## Current task surface

The canonical JSON surface intentionally exposes semantic LAS fields instead of
opaque blobs wherever the LAS 1.4 specification defines them directly:

- public-header fields, including validated stored modern counters, extents, and
  offsets
- all point formats 0 through 10
- standard LASF_Projection CRS records
- LASF_Spec records for classification lookup, text area description, extra
  bytes, waveform packet descriptors, waveform data packets, and the
  `Superseded` (LASF_Spec / 7) sentinel
- unknown VLR/EVLR payloads as base64

GeoTIFF key contents are modeled at the LAS-layer record structure level rather
than by implementing the full external GeoTIFF standard.

The intra-packet padding rule for waveform data (the spec line that requires
non-byte-aligned waveform samples to pad each packet to an even byte boundary)
is intentionally out of scope: the canonical JSON treats waveform packet bytes
as opaque, so packet-internal alignment is not validated.

## Reference language

LAS ships a Python reference implementation only. C++ is the CLISpecBench
default, but LAS 1.4 inspect/render needs little raw byte-twiddling beyond
`struct` and base64; a Python reference keeps the corpus readable, matches the
language footprint of the existing Python-only evals (GEDCOM, MARC21), and
avoids dragging in CMake just to demonstrate a parser. Adding a C++ reference
later is welcome; it is not required to evaluate Python submissions.
