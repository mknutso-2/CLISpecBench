I need a local tool for checking and rewriting MARC 21 bibliographic records.

Please build a command-line program that can:

- inspect a MARC record from a request file and emit a canonical
  machine-readable representation
- render that canonical representation back into MARC ISO 2709 bytes
- render that canonical representation as MARCXML
- reject malformed records with a clear structured error

The MARC rules for this task are in the `docs/` directory. The request and
response file contract is in `technical-requirements-prompt.md`.
