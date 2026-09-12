# GEDCOM 4.0.2 validation — 2026-09-12

This hidden-test and reference patch preserves every model-visible prompt and
supplied documentation byte. The public `FamilySearchGEDCOMv7.html` already
settles both requirements repaired here:

- §§1.3 and 3.1 expressly make a record's xref optional when no structure points
  to that record. The xref slot in the grammar specifies eligibility rather
  than mandatory presence. Seven old rejection cases for FAM, INDI, OBJE, REPO,
  SNOTE, SOUR and SUBM contradicted that prose. Their replacements inspect legal
  unreferenced records and observe the matching record with an absent/null xref.
  Required pointer resolution and unique identifiers remain separate tests.
- §3.2.2 FAMILY_RECORD requires a FAM.HUSB or FAM.WIFE link to have a matching
  direct INDI.FAMS link, and FAM.CHIL to have a matching INDI.FAMC link. Four AGE
  positives and four HUSB/WIFE official-fragment inspect/render positives had
  invalid supporting INDI records without those backlinks. Fixtures now supply
  them. The official fragment itself is unchanged; only synthesized pointer
  targets receive the necessary family context.

The missing-AGE and legacy-AGE rejection fixtures receive the same repair, so
an unrelated missing backlink cannot earn their rejection points. Six new
inspect/render cases exercise HUSB, WIFE and CHIL reciprocity directly. Each
first accepts its own valid counterpart and then removes only the named link;
there is no shared generic interface gate. Existing schema tests remain intact.
The reference now accepts optional unreferenced identifiers and validates the
explicit FAM-to-INDI backlink requirement on both actions. `@VOID@` has no target
record and remains exempt. Subordinate event-level FAMC has different public
semantics and is not subjected to the direct family-member rule.

Validation used offline Docker image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`,
a read-only repository mount and disposable source copies. Full results:

| Implementation | Previous 4.0.1 grade | Corrected 4.0.2 grade |
| --- | ---: | ---: |
| Corrected Python reference | — | 212/212 |
| Retained GPT-6 Astra Max Python | 191/206 | 212/212 |
| Retained GPT-5.6 Terra Max Python | 185/206 | 205/212 |

The old reference fails all 13 selected optional-xref/backlink controls, proving
both prior reference mistakes are detected. Terra passes all six new backlink
controls. Its remaining seven failures are substantive missing DATE_EXACT,
latitude/longitude bounds (two), SNOTE payload, family-event HUSB AGE, and empty
INDI inspect/render validation. The AGE defect was previously masked by the
fixture's missing backlink: repairing the context removes that false credit.
Thus this correction both restores legitimate passes and exposes a real
previously hidden failure; it is not an adjustment to favor a particular model.

The suite has 212 tests, with no skips or errors in these full runs. The hidden
suite hash is
`1f72aa246ff6b488fd0ce23b00d28f93561458aaebfb9e0a2fb6bdabc1721cc7`.
Ruff and strict Pyright pass on the changed test/helper files. The public prompt
content tree was compared byte for byte with the active 4.0.1 checkout and is
identical. Original model source, transcript, telemetry and grading artifacts
were not changed; the measurements above are isolated validation evidence,
with official regrades recorded separately when published.
