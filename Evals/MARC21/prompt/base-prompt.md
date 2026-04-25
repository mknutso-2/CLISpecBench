I need a local tool for checking and rewriting MARC 21 bibliographic records.

Please build a command-line program that can:

- inspect a MARC record from a request file and emit a canonical
  machine-readable representation
- render that canonical representation back into MARC ISO 2709 bytes
- render that canonical representation as MARCXML
- reject malformed records with a clear structured error

The MARC rules for this task are in the `docs/` directory. The request and
response file contract is in `technical-requirements-prompt.md`.

I only need Unicode MARC records for this tool. ISO 2709 payloads should be
treated as UTF-8 encoded text; do not implement MARC-8 character-set
conversion. The leader and directory entries are ASCII structural bytes, but
the control-field and data-field payload text must decode as UTF-8. If a
record contains field payload bytes that are not valid UTF-8, reject the
record as a malformed MARC record. When rendering ISO 2709 from the canonical
record, encode string values as UTF-8 field payload bytes.

When the MARC 21 bibliographic documentation for a field defines indicator
values, subfield codes, or repeatability, treat those definitions as validation
rules and reject records that violate them.
