I need a local tool that can inspect and rewrite FamilySearch GEDCOM files for a
family-history workflow.

Please build a command-line program that can:

- read a GEDCOM dataset from a request file
- inspect it and report a canonical machine-readable tree representation of the
  GEDCOM records and nested structures
- render that canonical tree representation back into GEDCOM text
- reject malformed datasets with a clear structured error

The GEDCOM rules for this task are in the `docs/` directory. The request and
response file contract is described in `technical-requirements-prompt.md`.
