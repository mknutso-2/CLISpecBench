# GEDCOM 4.0.3 validation — 2026-09-12

This tests-only patch isolates the existing positive VOID-pointer case from
unrelated family-link state. All 212 scored case identities are preserved.
The four files under `Evals/GEDCOM/prompt/` and the unchanged Python reference
were compared byte for byte with 4.0.2; no model-visible input changed.

The supplied `prompt/docs/FamilySearchGEDCOMv7.html` §1.3 (`#lines`, lines
495–496) defines `pointer = voidPtr / Xref` and `voidPtr = "@VOID@"`.
Section 3.1's pointer metasyntax expressly permits the VOID alternative.
The replacement fixture is a complete HEAD/GEDC/VERS 7.0 and TRLR document
with one `FAM` containing `WIFE @VOID@`. Its assertion finds the decoded
family and WIFE child and requires the exact `@VOID@` payload. Returning an
empty dataset or silently discarding the pointer cannot earn a pass.

The former fixture replaced a full family's WIFE pointer but retained the
former partner's `INDI.FAMS` link. Astra C++ rejects that combination because
it additionally requires a partner named by FAMS to appear as HUSB or WIFE.
The public §3.2.2 `#FAMILY_RECORD` text (line 659) explicitly requires the
opposite direction: a FAM.HUSB/WIFE reference must have a matching INDI.FAMS
backlink. The `#FAMS` definition calls it the family in which an individual
appears as a partner, but does not state the converse with the same explicit
requirement. This patch does not adjudicate that separate interpretation or
claim the old family document is unequivocally valid or invalid. It removes
that dependency from a test intended to measure VOID-pointer support.
Dedicated tests of the explicit family-to-individual backlinks are unchanged.

Validation used disposable source copies, a read-only repository mount,
`--network none`, and Docker image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`.
No inference was used for these comparisons.

| Implementation | 4.0.2 | 4.0.3 |
| --- | ---: | ---: |
| Unchanged Python reference | 212/212 | 212/212 |
| GPT-6 Astra Max C++ | 211/212 | 212/212 |
| GPT-6 Astra Max JavaScript | 212/212 | 212/212 |
| GPT-6 Astra Max Python | 212/212 | 212/212 |
| GPT-5.6 Sol Max Python | 205/212 | 205/212 |
| GPT-5.6 Terra Max Python | 205/212 | 205/212 |
| GPT-5.6 Luna Max Python | 201/212 | 201/212 |

All seven full runs collected 212 tests without skips or errors. All six
retained-submission comparisons have identical case identities. The only
changed outcome is Astra C++'s `test_void_pointer_is_allowed`, from fail to
pass; all existing Sol, Terra and Luna failures remain identical.

Two independent mutations of disposable reference copies verify the focused
observation. A variant that rejects VOID fails the successful-inspection
assertion. A variant that accepts the document but replaces its decoded VOID
payload with null fails the exact-payload assertion. Each selected run fails
only that targeted case, with the other 211 cases deselected. These controls
exercise the intended capability rather than a shared schema prerequisite.
Ruff and strict Pyright pass on the edited test file. Independent peer review
confirmed the minimal fixture's public-contract validity and non-vacuous
assertion; no reference change was needed.

The final hidden-suite SHA256 is
`de8bb17fdab7b7a28fc3fde0b60dbc51e8827d8fe54d9f42ac124825913e14a6`.
Original source, transcript, result JSON and telemetry were untouched. These
isolated measurements support separate official regrades; they do not rewrite
historical generation records or imply complete coverage of all GEDCOM limits.

A future public clarification may state whether direct INDI.FAMS links must
also have a corresponding FAM.HUSB/WIFE slot, including the intended treatment
of an unknown partner represented by VOID. Such a change should be explicit
and scored separately from basic VOID-pointer support.
