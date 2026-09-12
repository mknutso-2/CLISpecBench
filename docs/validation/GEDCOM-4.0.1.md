# GEDCOM 4.0.1 validation — 2026-09-11

All model-visible prompt and documentation bytes are preserved. This patch
repairs hidden fixtures, observations, and reference behavior, with no change
to the public GEDCOM or request contract.

The supplied `FamilySearchGEDCOMv7.html` provides the controlling requirements:

- `#structures`, §1.2: every structure requires a nonempty payload or a child;
  HEAD/TRLR/CONT are pseudo-structures with their own rules. Several official
  snippets illustrate lines or fragments rather than complete datasets. Their
  synthesized pointer targets were empty INDI/FAM/SOUR records; the single-line
  cb5 example was also used as an empty complete record. Fixtures now provide
  legal ordinary content. Empty DATE remains a legal datatype choice only with
  a permitted child (the fixture now supplies PHRASE).
- `#characters`, §1.1: an initial U+FEFF BOM has no semantic meaning.
- `#lines`, §1.3: CR, LF and CRLF are permitted line terminators; CONT joins a
  parent's payload and doubled initial @ escapes a literal @.
- The technical contract represents ordered records/children with explicit
  payload and pointer content. Merely returning exit 0 and any JSON was not
  evidence that official examples were decoded.

Official parse cases now compare the named example's semantic nodes, excluding
synthetic HEAD/TRLR and pointer targets. Missing null fields or empty children
lists do not repeat the separate schema gate. The fixture transcription helper
only decodes trusted fixture lines: it keeps a level-indexed parent stack,
folds CONT into `stack[level - 1]`, and removes one @ only from leading `@@`.
The reference passing these comparisons checks the helper against an
independent parser, including the multiline cb43 fixture.

Official render cases now start with known fixture trees rather than the
submitted parser's output. Parser failure therefore cannot skip render
coverage. The comparisons normalize only initial BOM and permitted EOL forms;
they preserve payload spacing, escaping, line order, and all other text. The
reference now ignores an initial BOM and enforces §1.2 on inspect and render.
Dedicated tests own those rules. Response files are cleared before each call.

Validation used offline Docker image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`
with a read-only repository and disposable reference copy. The corrected
Python reference passes **206/206**. The first added empty-record control
exposed a real reference omission (203/204 before the additional render/BOM
cases); the reference was corrected instead of relaxing the public invariant.
Test-suite hash:
`4580910f1f5cdc566e08c340922aed4926cdf5c95f1c8f68c63fe044d2ac5c04`.
Ruff and strict Pyright pass for changed tests and the Python reference.

A legal-output control wraps the corrected reference to emit initial BOM plus
CRLF on render. All **48/48 parse/render cases** pass, including the two
whole-tree roundtrips. This establishes that the repaired comparisons accept
that public serialization choice. It also exposed the original reference's
missing BOM support during validation. Old-suite comparisons against the
corrected reference additionally encounter the old invalid empty-record
fixtures, so those aggregate numbers are not presented as an isolated EOL effect.

The 2026-04-27 changelog investigation noted 32 Y-or-NULL payload cases failing
as a family. Those are distinct record/tag requirements and remain separately
visible; arbitrary reweighting based on which implementations happened to miss
a general rule would be unjustified. Raw failures are correlated evidence,
not a count of independent defects. The public base prompt's stale reference
to a standalone technical-requirements file remains a packaging clarification
for a future public-input revision. No historical model sources were available
locally, so no new historical model grades are claimed here.
