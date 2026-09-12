# IGES 1.0.17 follow-up scoring audit — 2026-09-12

Final test suite SHA-256:
`d3a6b066f602d4dd59fb51eb87a7e59d8e1c88d5eee803dcb1330765088514cb`.

All model-visible files are unchanged from 1.0.16. The hidden suite has **261
cases**, one more than 1.0.16: a focused malformed-Hollerith rejection paired
with a valid defaulted-string control. Historical generated source can be
regraded without new inference. The five conflicting direct analytic-offset
cases deferred in 1.0.16 remain deferred; this revision does not claim coverage
for them.

## A shared invalid input caused 69 correlated failures

The frozen reader corpus contained `0H` in optional Global field 25 (model
timestamp) in every one of its 44 documents. The captured Python reference
writer emitted this syntax, its reader accepted it, and the original independent
physical check inspected entity records but omitted Global string grammar.
That validation gap allowed an invalid common prerequisite to survive 1.0.16.

Public §2.2.2.3 requires a **nonzero** unsigned Hollerith character count.
An empty field receives the implicit NULL string default under §§2.2.2.3 and
2.2.3. Only that token is replaced by an empty field; Global records are repacked
and Terminate counts refreshed. Paired semantic documents, their identity keys,
and every Start, Directory and Parameter record remain unchanged.

An independent scanner now validates Hollerith boundaries across joined Global
physical records. It skips over string bodies, so delimiters inside strings do
not become field boundaries, and honors the public permission for comments
after the record delimiter. The existing default-global writer test uses this
physical gate before parsing: a writer and reader sharing the same `0H` bug
cannot earn that point together. The new reader gate uses a separate raw Global
input and a legal NULL-string control; it has no writer or geometry prerequisite.

The preserved Astra Python submission initially scored **170/260**. Correcting
only this shared Global syntax raised it to **239/260**: 69 failures arose from
one invalid common fixture, rather than 69 independent implementation defects.

## Remaining invalid positive prerequisites

All 21 remaining failures at that point were missing positive cross-references:
11 annotation cases, five solid cases, one pointer/logical data-type case, two
spline/FEA cases, and two structure/view cases. Repairs retain focused target
observations rather than comparing every support field:

- Annotation note, witness, leader, curve and symbol pointers now resolve to
  real records with the required annotation/dependency flags. Witnesses have
  IP1, odd counts and collinear points (§4.10). Angular leader endpoints lie
  on their named circle with the specified orientations (§4.55); curve
  dimension leaders meet the referenced curved endpoints (§4.56).
- GeneralLabel210 requires at least one leader (§4.59). Its old zero-leader
  positive is renamed `test_general_label_with_leader_roundtrip`, retaining
  one case. FlagNote208's separately permitted empty leader list remains.
  Type216 inputs contain exactly their five public pointer fields, without the
  former unscored `xt`/`yt` extras. SectionedArea230 has a closed outer circle
  and two disjoint strictly contained islands.
- Solid162 has a coplanar open profile whose projections onto the axis close
  a positive-area rectangle (§4.43); Solid164 has a simple closed circle and
  noncoplanar extrusion (§4.44). Boolean180 has real acyclic solid operands
  (§4.46), SelectedComponent182 selects a point strictly within one component
  (§4.47), and Assembly184 contains actual solids and transformations (§4.48).
- The negative color pointer resolves to a Color314, and the Face boolean uses
  the already independently validated open triangular shell, not an empty
  Face510 with null surface/loop references (§§4.76 and 4.143–4.147).
- ConnectPoint132 has an actual symbol, two dependent text templates, and a
  NetworkSubfigure320 owner (§4.26). Its display line has one physical parent;
  the owner references the ConnectPoint instead of also owning that line.
- FiniteElement136 uses seven actual cube-corner Nodes, labeled Cartesian
  Form10 coordinates, and matching node/element subscripts. The eighth null
  pointer explicitly represents the missing node permitted by §4.28.
- Drawing404 contains actual logically dependent Views and a physically
  dependent note (§4.96). Drawing/View use annotation, including the matrix
  used solely for annotation (§2.2.4.4.9.3). Array412 references a real Line
  (§4.136). Only the relevant Drawing/Array fields are compared.

## Reference defects exposed by legal inputs

Python and JavaScript formatters now default empty strings and reject `0H`.
Their Type216 parser/writer previously consumed/emitted nonexistent `xt`/`yt`
fields beyond the five public pointers; both are corrected. C++ already wrote
legal empty strings and the five-pointer Type216 layout, but its
`next_string_or` discarded malformed-token errors and silently defaulted them;
it now propagates errors. C++ View410 deserialization also incorrectly required
inactive perspective fields for Form0. It now requires only the active form's
fields, as the technical requirements explicitly allow inactive defaults.

These fixes affect references only. No generated submission was changed.

## Validation and independent review

All grading used Docker image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`,
with networking disabled, repository/candidate mounts read-only, and disposable
copies of implementation source. Final corrected references and the preserved
Astra submission each score **261/261**. The unchanged Python reference scores
**258/261**, failing exactly the zero-count reader gate, default-global writer
physical gate, and corrected Type216 input. This preserves evidence of the
reference bugs rather than treating references as the normative oracle.

Independent reviewer `audit_records` verified the annotation/solid graphs and
geometry against the public corpus: **27 fixtures, 77 entities, 50 pointer
edges**, including real targets, acyclic Boolean structure, annotation child
flags, witness collinearity, arc radii/endpoints, island containment and
selection within exactly one solid. It also reviewed the display/FEA/data-type
contexts and identified the final use-flag and single-parent corrections above.
The parent reviewer independently confirmed the original `0H` rejection and
reviewed the source and complete Astra transcript.

Seven disposable parse-output mutations each corrupt one targeted observation:
color pointer, ConnectPoint function name, FEA node pointer, Drawing angle,
Array flag, Type216 witness pointer, and Boolean operator. All seven respective
cases fail at their intended semantic assertion. Correct source passes them.
The independent Hollerith scanner accepts embedded delimiters and trailing
comments, and rejects zero counts and truncated strings. Ruff and strict
Pyright pass. Local reports and reproducible offline runners are retained in
`work/iges-followup/`; no mutation touches preserved model source.

Maintenance commands from the repository root:

```bash
uv run python Evals/IGES/tests/validate_reader_fixtures.py
uv run python Evals/IGES/tests/validate_topology_fixtures.py
```

The reader check covers all **44 documents / 117 entity records**, now including
Global Hollerith grammar. Existing 1.0.16 topology/analytic mutation evidence and
public floating tolerances remain applicable; no tolerance was changed here.

## Remaining limits and public cleanup

The explicit roundtrip cases still depend on both writing and parsing, and legal
support records remain prerequisites. Frozen inputs eliminate the writer
prerequisite for reader/evaluation cases; they do not make every underlying
file section or entity type independent. Failed-case counts must not be reported
as counts of independent bugs. A perfect score establishes this suite's covered
observations, not complete IGES conformance.

The supplied §4.134 View Directory table is visibly misaligned and conflicts
with the explicit general prose assigning View/Drawing Entity Use Flag01.
The fixture uses that clear general rule, while its scored assertions observe
view data rather than forcing a disputed status interpretation. Repair the
transcribed public table in a later public revision. Detailed drafting sections
absent from the supplied specification remain limited to the public technical
appendix contract. The five analytic-offset conflicts and other public
limitations documented in `IGES-1.0.16.md` remain unresolved public work.

Integration normalized import-group blank lines in three test files. Their
Python ASTs are identical before and after formatting. The pre-format reference
validation hash was `f28a8819bde4d3e209fb860fdb26bd1013686ff13c750e003a2a2070805df3d7`; the committed suite hash above includes only that nonsemantic formatting change.
