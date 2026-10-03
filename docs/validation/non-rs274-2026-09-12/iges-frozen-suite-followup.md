# IGES frozen-suite follow-up for a future revision

October 2, 2026. Findings from Terra Max IGES JavaScript UID
`0a060678-8ff5-4acb-814a-dcc3176ede71`, observed score **228/249** under IGES
1.0.21. Preserve that frozen result and annotate the review; do not change tests,
prompts, scoring or submitted source during the current collection. This follows
the user's direction to document eval fixes for later and continue collection.

## Numeric fields split by fixture packing

The supplied specification, section 2.2.3 (line 450), constrains a numeric field's
end and delimiter to the same physical line, but is less explicit about where
the field starts. Global and Parameter Data widths are 72 and 64 data columns
respectively. Strings have an explicit continuation rule. The submission reads
this as prohibiting split numeric tokens; the technical prompt's verbatim
concatenation rule does not explicitly settle that interpretation.

`tests/raw_iges_support.py:52-55` slices the Global payload every 72 characters
without respecting numeric token boundaries. Some frozen reader fixtures likewise
split numeric fields. The JavaScript submission rejects those physical records
before reaching the semantics named by the tests. Treat this as a fixture/contract
ambiguity, not an independently settled standards violation. Independent static
review maps 17 observed failures to this boundary restriction: six raw Global
fixtures, ten entity-reader fixtures, and one diagnostic case whose disputed
packing hides the intended nonpositive-field diagnostic. Do not describe these
as 17 proven geometry, defaulting, version-clamping or string-parser defects.
The run-specific review retains the exact case/token mapping.

Future fix: use a spec-aware fixture packer that keeps a numeric field and its
delimiter together, regenerate only affected physical fixtures, and add focused
positive/negative controls for numeric boundaries and legal string continuation.
Validate fixtures independently of submission/reference writers. Pack fixtures
valid under both interpretations and explicitly state any intended tolerance
for split numeric fields.

## Legal empty association/property tails rejected by writer assertions

Sections 2.2.3 and 2.2.4.5.2 allow standard additional association/property groups.
Their zero counts may be written explicitly as `0,0`, or defaulted by terminating
the record earlier. Omission is permitted, not mandatory.

Three frozen assertions wrongly interpret the legal trailing zero counts as
entity data or demand their absence:

- `test_property_bool_values_serialize_as_logical`
- `test_real_values_in_parameter_records_are_spec_legal`
- `test_line_parameter_record_has_entity_type_prefix_and_expected_field_count`

The observed Boolean data are correctly serialized as `1,0`; the first assertion
mistakes the following standard tail for additional Boolean data. Future tests
should identify entity-specific data separately from legal standard groups and
accept explicit/defaulted zero tails, with controls for malformed counts/pointers.

## Genuine defect and revision policy

The remaining JavaScript failure accepts a zero-length Hollerith `0H`, contrary
to section 2.2.2.3's nonzero count requirement. Keep that model defect distinct
from the 20 fixture/assertion observations above. Python's two failed cases also
concern genuine reader/writer `0H` behavior, not these legal-tail assertions.

Implement no repair or adjusted score in this note. A later revision needs the
normal author-eval workflow, independent oracle review, reference/control
validation, version/changelog updates and preserved-original saved-source
regrades. Raw scores and accounting must remain auditable across that revision.

## Luna C++ follow-up: physical-line assumptions and missing AVDT mapping

October 2, UID `0e6736d8-b82a-4178-bfc2-cd4245159e8d`, frozen **231/249**.
Three writer checks examine only the first 64-column P data fragment:
`test_real_values_in_parameter_records_are_spec_legal`,
`test_line_parameter_record_has_entity_type_prefix_and_expected_field_count`,
and `test_parameter_records_use_selected_custom_delimiters`. They require the
record terminator on that first line before checking the intended semantics.
The submitted writer uses verbose scientific notation, producing multiple P
records. Multi-line entity data is not itself prohibited; these assertions
cannot establish the claimed formatting/delimiter defect. This is distinct from
Terra's explicit empty association/property tails above. The C++ writer also
blindly slices numeric fields across physical boundaries, so this caveat does
not certify its packing as conforming. A future test should reconstruct the
complete logical entity record, validate numeric spelling/value and delimiters,
and separately test physical packing against clarified public requirements.

Two Type322 Form1/Form2 roundtrips fail an AVDT-to-FieldValue mapping mismatch.
The supplied technical prompt gives `avdt` range 0–6 and says it selects the
value kind, but omits the numeric mapping; the supplied spec explicitly omits
section4.79. The submission maps1→real,2→string,3→pointer, whereas the fixtures
expect1→integer and2→real. Record the disagreement, but do not characterize it
as violating a fully supplied mapping table. A later public-input revision
should supply that table and examples, then independently validate focused
positive and negative controls. Keep both observations and the frozen score;
no adjusted score, test repair or model-input change is made here.

The other13 observations map to concrete reader/writer defects, including
Type213/312 field ordering, Type146/148 time ordering, generic Type406 kind
loss, illegal0H, missing Type408 scale default, and Type212 real dimensions
parsed as integers. Several observations share supporting Type312 failures;
do not count every failed test as an independent defect. The portable per-run
review records the exact mapping and offline diagnostic evidence.

## Luna Rust follow-up

October 2, UID `a9369c42-9c26-46e5-bd16-34be8138eb68`, frozen **239/249**.
The same two AVDT mapping disagreements and three first-physical-P-line
assertions occur here. Rust's Parameter packer keeps ordinary numeric tokens
and their delimiters together; verbose scientific notation still places the
logical record terminator on a later physical line. Reconstruct the complete
logical record in the future tests; do not demand single-line output.

The other five observations are concrete implementation failures: accepting
and emitting illegal `0H` (two), always selecting the first composite-curve
constituent (two), and rejecting the appendix's legal defaulted Global
delimiters (one). The latter was independently reproduced in the pinned offline
grader: the parser skips both default commas, misreads `8HPANEL123` as the
record-delimiter declaration, and reports `invalid global record delimiter`.
It is not an EOF-newline failure. Preserve all ten outcomes and the original
score; no tests, public inputs or submission sources are changed here.
