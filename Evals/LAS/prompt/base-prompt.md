I work with airborne lidar data and need a small program that understands LAS
1.4 files.

Please build a program that can do two things:

1. inspect an existing LAS 1.4 file and turn it into a structured JSON
   description
2. render a LAS 1.4 file from that JSON description

The behavior should follow the official LAS 1.4 documentation in `docs/`. I
care about the file structure and metadata defined there, including:

- the public header block
- variable length records and extended variable length records
- coordinate reference system records
- point record formats 0 through 10
- waveform-related records and point fields
- extra-bytes metadata

When the input file or dataset violates the LAS 1.4 rules in the documentation,
the program should report that as an error instead of silently accepting it.
This applies to the standard `LASF_Spec` and `LASF_Projection` records too:
when one of those records is structurally malformed or describes content that
contradicts the rest of the file, treat the whole inspected file as invalid
rather than quietly downgrading the bad record to opaque metadata.

Two areas are intentionally out of scope and should not drive errors: the
ESRI WKT dialect of the OGC WKT records, and the internal layout of each
waveform packet (per-packet sample layout and the spec's even-byte padding
rule for non-byte-aligned `bits_per_sample`). Waveform packet bytes can be
treated as an opaque payload that round-trips between inspect and render.
