# Deferred public-input clarifications — 2026-09-12

This inventory consolidates the seven task validation reports and checks their
statements against the supplied public corpus and current hidden tests. It
proposes a later public-input revision; it does not change prompts, documents,
tests, references, results, or the authority used for existing scores. No
external specification was substituted for the files supplied to the models.

The current revisions are WordCount **1.0.4**, LAS **2.0.4**, GEDCOM **4.0.3**,
MARC21 **3.0.2**, BibTeX **1.2.4**, ICal **3.0.2**, and IGES **1.0.17**. GEDCOM
4.0.3 is integrated in commit `e6a13bf`; its minimal VOID fixture is therefore
current behavior, not a pending proposal. Each task's model-visible inputs
remain unchanged through these scoring repairs.

**Decision** means the supplied contract leaves a behavioral or representation
choice open. A future requirement must state that choice explicitly and should
be tested using new generations that received it. **Cleanup** means existing
precedence or an explicit permission already determines the treatment; the
public wording can be made clearer without inventing a new rule. Removing an
existing permission is a decision even when retaining it needs only cleanup.

## WordCount 1.0.4

Evidence: [WordCount validation][wc-validation].

1. **Decision — non-ASCII casing and ordering.** The [word-count specification,
   lines 11, 29 and 35][wc-spec] requires lowercase words and lexicographic ties,
   but does not define Unicode case folding, normalization, locale, collation,
   or a Unicode version. Current ranking/case probes use ASCII; Unicode probes
   observe only byte counts and the explicitly exhaustive six delimiters.
   **Proposed wording:** specify the casing transformation and tie comparator
   together. One possible bounded policy is “map ASCII A–Z to a–z, preserve all
   other characters, and compare the resulting UTF-8 byte sequences”; choosing
   Unicode folding instead needs a named algorithm/version. Neither choice is
   imposed on prior submissions.
2. **Decision — input encoding and malformed text.** The [exit-code contract,
   lines 22–26][wc-tr] calls malformed input an invocation error without defining
   an encoding or malformed byte sequences. Valid UTF-8 fixtures do not imply a
   hidden invalid-UTF-8 rejection policy. **Proposed wording:** identify allowed
   encodings and the required behavior for invalid sequences, while retaining
   the specification's byte-based `characters` count. For example, explicitly
   choose UTF-8 with invalid sequences producing exit 1, or define arbitrary
   byte input and its JSON representation.

## LAS 2.0.4

Evidence: [initial audit][las-201], [representation repairs][las-202],
[explicit short-tail repair][las-203], and [deprecated-bit repair][las-204].

1. **Decision — unknown render JSON members.** The [technical schema][las-tr]
   specifies known fields but no unknown-key policy. The hidden suite no longer
   demands rejection for extra color fields on an otherwise non-color format,
   and positive inputs no longer require accepting the private `_evlr_hint`
   member. **Proposed wording:** explicitly permit ignoring unknown members or
   require a structured error; keep known-field validation independent.
2. **Decision — empty-dataset bounds.** Header recomputation is required by
   [technical requirements, lines 107–123][las-tr], while the [LAS extrema
   definition, around line 610][las-layout] does not define extrema of zero
   points. `test_render_empty_point_list_round_trips` excludes only the six
   bounding doubles from its physical comparison. **Proposed wording:** state
   the six values to emit for an empty dataset, or explicitly allow any finite
   bounds in that case. No particular values are currently scored.
3. **Decision — terminal NUL in GeoASCII JSON.** [Technical requirements,
   lines 216–217][las-tr] expose `text`; the [GeoASCII storage rules, around
   line 1535][las-layout] do not settle whether a terminal wire NUL belongs in
   that JSON string. Tests accept the exact text or removal of one terminal
   NUL and tolerate the corresponding single added render terminator; embedded
   content and key offsets remain exact. **Proposed wording:** say explicitly
   whether `text` includes the terminator, and how render handles an already
   terminated value. Arbitrary whitespace/NUL stripping is not permitted by
   the current comparisons.
4. **Decision — sparse classification lookup representation.** [Technical
   requirements, lines 199–201][las-tr] give an entries array and define omitted
   descriptions on render, but do not mandate sparse inspect output. Tests
   normalize omitted versus explicit empty descriptions while checking class
   numbers, duplicates, and actual text. **Proposed wording:** explicitly permit
   both sparse and complete 256-entry output, or name one canonical shape.
5. **Decision — inspect output for an absent waveform.** The [waveform schema,
   lines 155–168][las-tr] specifies zero wire fields when an optional render
   object is absent, without requiring inspect to materialize that object.
   Tests accept omission or the complete seven-field zero object and still
   require the expected points. **Proposed wording:** say whether inspect omits
   a no-waveform object or emits its zero representation; permitting both
   preserves the current scoring policy.
6. **Decision — render defaults for omitted Extra Bytes.** [Technical
   requirements, lines 181–184][las-tr] expose trailing bytes but do not define
   whether missing `extra_bytes_b64` is zero-filled to a declared descriptor.
   The negative now supplies `AQ==` explicitly: a one-byte tail cannot contain
   the declared two-byte unsigned short. Omission itself is unscored.
   **Proposed wording:** define whether a missing tail is empty, synthesized, or
   erroneous when descriptors require bytes; keep explicit short tails invalid.
7. **Decision — clear deprecated internal-waveform bit.** [LAS Table 4,
   lines 489–495][las-layout] describes the internal bit as deprecated; the
   [header offset definition, lines 613–617][las-layout] separately locates the
   internal EVLR. These do not unequivocally require rejecting an otherwise
   coherent internal record just because bit 1 is clear. The 2.0.4 case instead
   sets external-storage bit 2 while retaining internal data, an explicit
   contradiction under the [base prompt, lines 20–25][las-base]. Bit-clear-only
   acceptance/rejection is unscored. **Proposed wording:** state whether a
   nonzero internal offset may identify deprecated internal storage with bit 1
   clear, and distinguish it from the prohibited external/internal conflict.

The 60-byte waveform EVLR header offset, explicit packet bounds, and opaque
waveform payload treatment are already defined; they are repaired test
preconditions, not new public-policy choices.

## GEDCOM 4.0.3

Evidence: [4.0.1 validation][gedcom-401] and [4.0.3 validation][gedcom-403].

1. **Decision — converse family reciprocity.** The supplied [GEDCOM HTML,
   §3.2.2 `#FAMILY_RECORD`, line 659][gedcom-spec] explicitly requires
   `FAM.HUSB/WIFE → INDI.FAMS` and `FAM.CHIL → INDI.FAMC` backlinks. Its `#FAMS`
   definition describes a partner's family without imposing the converse slot
   rule as explicitly. Current `test_void_pointer_is_allowed` uses just a valid
   header, `FAM.WIFE @VOID@`, and trailer, requiring that exact decoded pointer.
   It has no former partner's retained `FAMS` link. Explicit forward backlink
   tests remain. **Proposed wording:** decide whether every `INDI.FAMS` requires
   a matching `FAM.HUSB/WIFE` slot, including unknown/VOID partner contexts, and
   score that separately. Basic VOID syntax is already explicit in `#lines`
   (§1.3, lines 495–496) and §3.1; it needs no new rule.
2. **Cleanup — assembled-document reference.** The [base prompt, lines
   17–18][gedcom-base] refers to `technical-requirements-prompt.md` as a separate
   file although the run supplies the assembled requirements. **Proposed
   wording:** point to the included requirements section or ensure that exact
   filename is provided. This is packaging clarity, not a scoring choice.

Unreferenced optional xrefs and the explicitly required family-to-individual
backlinks were already defined in the public source. They may deserve more
prominent examples, but their repairs do not require a new semantic decision.

## MARC21 3.0.2

Evidence: [MARC21 validation][marc-validation].

1. **Decision — minimum length for variable-length 007 c/m.** The [007 overview's
   variable-length note][marc-007], [007 c Input Conventions, around line
   1091][marc-007c], and [007 m Input Conventions, around line 1676][marc-007m]
   say the first six/eight positions “should always” be present, without clearly
   making a two-character or six/eight-character minimum mandatory. Current
   positives use recommended six/eight lengths and the maximum; undersized c/m
   acceptance/rejection is unscored. Maximum lengths remain checked.
   **Proposed wording:** explicitly distinguish required minimum record length
   from recommended populated positions for these two categories.
2. **Cleanup — contradictory 357 example.** The [357 indicator table, lines
   55–56][marc-357] permits blanks; the first example around line 112 shows `#0`.
   The repaired corpus uses the following valid `##` example. It does not add
   `0` to the indicator vocabulary because of the contradictory illustration.
   **Proposed wording:** annotate the example as an erratum and identify the
   indicator table as governing, rather than silently altering the mirrored
   source. Accepting the contradictory example would require an explicit new
   exception.

## BibTeX 1.2.4

Evidence: [final summary-versus-WEB audit][bib-validation]. The [base prompt,
   lines 24–28][bib-base] and [summary introduction, lines 28–32][bib-summary]
give the supplied authoritative source precedence for ordinary disagreements.
That precedence is distinct from separately stated allowed approximations.

1. **Cleanup — ordinary summary contradictions.** Correct the following
   statements in the [supplied summary][bib-summary]: predefined months (§1.5,
   around line 96), name partition/extra-comma descriptions (§§2.2–2.5), nonzero
   `if$`/`while$` truth (§3.5, lines 325–326), space-joined `preamble$` (line 346),
   and mandatory short trailing-whitespace preservation (§3.6, lines 389–395).
   Current tests use explicit month `MACRO` declarations and follow the supplied
   [WEB][bib-web] for name slices, strictly positive conditionals, direct
   preamble concatenation, and line-buffer trimming. Canonical parity corpora
   contain at most one preamble, avoiding eight failures from that one focused
   behavior. **Proposed wording:** replace each conflicting description with
   the supplied WEB behavior and retain the existing authority statement.
2. **Cleanup, or decision if withdrawn — explicit permitted approximations.**
   Preserve and list the [summary's][bib-summary] exceptions: always-space
   separators within name parts (§2.6, around line 200), no-op `top$` (§3.5,
   line 361), load-time warning for quoted undefined names (§5.3, around line
   519), and the bounded ordinary-brace/deep-accent approximations (§8, around
   lines 563, 592 and 691). The focused `top$` test accepts exactly the pop
   result or the no-op result; no canonical style calls it. Quoted-unknown
   rejection is unscored. Width probes accept the documented brace alternatives,
   and a combined allowed name-spacing/brace-width variant passes all eight
   canonical parity cases. **Proposed wording:** “These enumerated permissions
   are exceptions to WEB precedence; all other disagreements follow WEB.”
   Requiring only faithful behavior would be a new contract, not an old-score
   correction.
3. **Decision — raw Unicode operator and label units.** The [summary §7,
   around line 558][bib-summary] mentions UTF-8 without fully specifying
   byte/codepoint semantics for raw Unicode names and labels. Canonical parity
   uses ASCII/TeX accent spellings; current substring/length probes that could
   select a unit use ASCII. Dedicated UTF-8 passthrough remains covered.
   **Proposed wording:** define which string operators count bytes or Unicode
   characters, and the corresponding label/truncation behavior, separately
   from TeX accent handling. Do not infer it from an oracle's host encoding.
4. **Cleanup — actual shipped version.** The [summary][bib-summary] calls the
   target 0.99c; the [supplied WEB banner, line 136][bib-web] is 0.99e. Its history
   at lines 40–46 distinguishes the 0.99d line-wrap change and 0.99e's
   nonfunctional cleanup. **Proposed wording:** identify the exact supplied
   source revision/hash and describe compatibility intentionally. Do not call
   an independently installed executable 0.99c merely because it is compatible.
5. **Decision — name-index warning mapping.** The supplied WEB retains the
   final scanned name and warns for a positive index beyond the list length.
   The [1.2.4 correction](../BibTeX-1.2.4.md) observes only that selected name.
   The public JSON catalog does not specify how to classify this warning;
   `bst_type_error` describes stack-type/default recovery, whereas this argument
   has the proper type. **Proposed wording:** explicitly assign a warning kind
   or permit an unmapped diagnostic. Until that public decision is made, do not
   score its warning kind, wording, count or absence. Native warning exit status
   2 also does not override the wrapper's successful warning-only exit status 0.

## ICal 3.0.2

Evidence: [3.0.1 validation][ical-301] and [3.0.2 validation][ical-302].

1. **Cleanup — spring-gap summary contradiction.** [Summary §5.1.1, lines
   365–374][ical-summary] mandates the post-transition offset; [RFC 5545 §3.3.5,
   around line 1896][rfc5545] uses the offset before a gap for an explicit
   nonexistent local time. The [base prompt][ical-base] and summary introduction
   give RFC precedence; the corrected test therefore requires the pre-gap UTC
   conversion. **Proposed wording:** state that RFC rule and distinguish an
   explicit local timestamp from nonexistent occurrences generated by a
   recurrence rule. This is already scored, not a deferred interpretation.
2. **Cleanup, or decision if narrowed — unresolved TZID alternatives.**
   [Summary §5.1.2, lines 376–391][ical-summary] explicitly permits structured
   hard rejection if documented in `--help`, or warning/continuation as a
   floating timestamp retaining the TZID. Both behavior paths remain accepted;
   host timezone lookup is prohibited by summary §12. Free-prose help disclosure
   remains a human-review obligation, not an arbitrary phrase-matching gate.
   **Proposed wording:** retain and enumerate both paths with example JSON;
   choosing one mandatory path would remove an existing permission.
3. **Decision — `line_too_long` reader warning.** The [technical warning catalog,
   around line 382][ical-tr] names the code; [RFC 5545 §3.1][rfc5545] recommends
   producer folding at 75 octets but does not require a reader warning. Current
   tests check exact decoded content at the boundary, above it, and after
   folding, with warning presence optional. **Proposed wording:** explicitly
   make this warning optional, or define its mandatory physical-line trigger,
   octet counting and treatment of folded lines.
4. **Decision — materializing implicit `RELATED=START`.** The [VALARM JSON
   schema, around line 164][ical-tr] permits `related: null`; [RFC 5545
   §3.2.14][rfc5545] supplies semantic default START. The implicit-parameter
   case accepts null or START, preserves the duration, and rejects END;
   explicit parameter values remain strict. **Proposed wording:** “Null denotes
   an omitted parameter with effective value START,” if preserving both output
   representations, or require canonical default materialization explicitly.
5. **Decision — empty identifiers versus missing-property warnings.** The
   [technical iTIP warning contract, around line 391][ical-tr] and [summary
   method requirements][ical-summary] describe property presence without
   settling the missing-warning treatment of present empty UID text. Repaired
   missing-UID fixtures omit the property; they do not impose an empty-to-missing
   conversion. **Proposed wording:** distinguish absent required properties
   from present empty/invalid values and name their warning/error codes.
6. **Cleanup and possible future intent decision — CANCEL status.** [RFC 5546
   §3.2.5][rfc5546] distinguishes whole-event cancellation from uninviting
   selected attendees, which may omit STATUS. Current fixtures provide named
   recipients and isolate required ORGANIZER; no negative infers whole-event
   cancellation solely from missing STATUS. **Proposed wording:** explain the
   two cases and avoid claiming that absent STATUS alone proves invalidity. If
   the CLI is to determine cancellation intent beyond available message
   context, specify how that intent is provided before scoring it.
7. **Decision — required RSCALE support and fallback scope.** The [technical
   schema][ical-tr] names `rscale_unsupported`; supplied [RFC 7529 §§4.3.1,
   4.3.3–4.3.4][rfc7529] provides concrete examples, but public task prose does
   not define the complete required calendar set or fallback scope. The existing
   warning plus preserved raw RRULE path remains accepted, including the
   historical Gregorian SKIP fallback. For the named Gregorian/Chinese/Hebrew
   expansion probes, the support path requires the complete expected sequence
   rather than just DTSTART; the Islamic-civil probe is parse-only.
   **Proposed wording:**
   list mandatory calendars/features and explicitly identify the cases where
   warning/preservation can replace expansion. Historical acceptance is not
   proof that this broad fallback was clearly documented to models.

## IGES 1.0.17

Evidence: [1.0.16 validation][iges-116] and [1.0.17 follow-up][iges-117].

1. **Decision — direct analytic surfaces as Type140 bases.** [Technical
   requirements §1.6, lines 232–244][iges-tr] expressly supports Type140 offsets
   over Types192/194/196/198, while the [supplied specification §§4.51–4.54,
   around lines 5157, 5243, 5330 and 5415][iges-spec] allows those surfaces to be
   referenced only by Face510. No explicit authority hierarchy resolves this
   conflict. Five direct analytic-offset cases are absent from collection and
   the denominator. The other analytic geometry cases retain legal Face/OpenShell
   contexts; independent Plane190 and plane-based offsets remain covered.
   **Proposed wording:** explicitly relax the Face-only restriction for these
   task-specific Type140 bases, or remove them from the supported base list.
   Either choice belongs in a new public-input revision.
2. **Cleanup, or decision if adding an alias — Type316 millimetres.** The
   [technical Type316 example, around line 1656][iges-tr] uses `MM`; the [supplied
   §4.77 unit table, around lines 6290–6304][iges-spec] gives `M` with a scale
   factor. Current positives use `M` with scale `0.001`, the common valid
   representation. No new negative rejects `MM`. **Proposed wording:** correct
   the example to `M`/`0.001`, or explicitly declare `MM` an accepted extension.
3. **Cleanup — View Directory table transcription.** The [general rule
   §2.2.4.4.9.3, around line 916][iges-spec] explicitly assigns annotation use to
   View/Drawing and matrices used only for annotation. The [§4.134 table,
   around lines 7793–7801][iges-spec] is visibly misaligned and conflicts with
   that prose. Fixtures use the clear general rule; scored comparisons observe
   view data rather than asserting a disputed table value. **Proposed wording:**
   annotate/correct the transcription and make its relation to the general rule
   explicit. This avoids an extra status gate, but is not a claim that a parser
   mechanically following the broken table will accept every positive fixture.
4. **Decision — scope of omitted FE/network/drafting sections.** The supplied
   [specification's omitted-section list and §3.7][iges-spec] and the [technical
   appendix][iges-tr] do not collectively expose every full-standard obligation.
   For example §3.7 mentions load-case General Notes, but Type418's JSON schema
   at lines 1863–1873 exposes node and tabular-property pointers with no such
   note slot. Current tests use those expressible typed fields with real support
   records and make no demand for an unexpressible General Note. **Proposed
   wording:** explicitly limit these entities to the appendix contract, or
   supply the omitted sections and expand the JSON schema. Do not infer full
   omitted-standard conformance from the present score.

The five deferred nodes are:

- `test_geometric_eval.py::test_offset_surface_over_cylinder_expands_radius_on_indicator_side`
- `test_geometric_eval.py::test_offset_surface_indicator_flips_global_normal_orientation`
- `test_geometric_eval.py::test_offset_surface_over_cone_uses_conical_reference_parameters`
- `test_geometric_eval.py::test_offset_surface_over_sphere_extends_radius_along_spherical_normal`
- `test_geometric_eval.py::test_offset_surface_over_torus_offsets_along_minor_circle_normal`

## Scoring boundary confirmed

The current test sources and validation reports support the accepted/unscored
treatments described above. Deferred choices are handled with inputs valid under
both readings, narrowly accepted alternative outputs, or removal of the
conflicting scored condition. They are not collected as skipped failures.
Ordinary BibTeX and ICal summary contradictions remain scored according to their
explicit public precedence; MARC357 and the IGES View transcription use the
clear tables/prose as described, rather than inventing new exceptions.

This is an inventory of identified ambiguities, not proof that every public
sentence or untested feature is complete. In particular, the RSCALE fallback's
historical scope and the IGES View transcription have the precise limits noted
above. Legal support records, common parser functionality, and explicit
roundtrips still create shared prerequisites. A failed-case total is not a count
of independent bugs, and a perfect score is not complete standard conformance.

For a later public revision, decide the open policies first, record the exact
new public-input hashes/version, and collect fresh generations under that
contract. Retain the current contract and provenance for fair old-source
rescoring rather than applying those new choices retroactively.

[wc-validation]: ../WordCount-1.0.4.md
[wc-spec]: ../../../Evals/WordCount/prompt/docs/wordcount-spec.md
[wc-tr]: ../../../Evals/WordCount/prompt/technical-requirements-prompt.md
[las-201]: ../LAS-2.0.1.md
[las-202]: ../LAS-2.0.2.md
[las-203]: ../LAS-2.0.3.md
[las-204]: ../LAS-2.0.4.md
[las-tr]: ../../../Evals/LAS/prompt/technical-requirements-prompt.md
[las-layout]: ../../../Evals/LAS/prompt/docs/17-030r1-layout.txt
[las-base]: ../../../Evals/LAS/prompt/base-prompt.md
[gedcom-401]: ../GEDCOM-4.0.1.md
[gedcom-403]: ../GEDCOM-4.0.3.md
[gedcom-spec]: ../../../Evals/GEDCOM/prompt/docs/FamilySearchGEDCOMv7.html
[gedcom-base]: ../../../Evals/GEDCOM/prompt/base-prompt.md
[marc-validation]: ../MARC21-3.0.2.md
[marc-007]: ../../../Evals/MARC21/prompt/docs/loc-bibliographic-html/bd007.html
[marc-007c]: ../../../Evals/MARC21/prompt/docs/loc-bibliographic-html/bd007c.html
[marc-007m]: ../../../Evals/MARC21/prompt/docs/loc-bibliographic-html/bd007m.html
[marc-357]: ../../../Evals/MARC21/prompt/docs/loc-bibliographic-html/bd357.html
[bib-validation]: ../BibTeX-1.2.3.md
[bib-base]: ../../../Evals/BibTeX/prompt/base-prompt.md
[bib-summary]: ../../../Evals/BibTeX/prompt/docs/summary.md
[bib-web]: ../../../Evals/BibTeX/prompt/docs/authoritative/bibtex.web
[ical-301]: ../ICal-3.0.1.md
[ical-302]: ../ICal-3.0.2.md
[ical-tr]: ../../../Evals/ICal/prompt/technical-requirements-prompt.md
[ical-summary]: ../../../Evals/ICal/prompt/docs/summary.md
[ical-base]: ../../../Evals/ICal/prompt/base-prompt.md
[rfc5545]: ../../../Evals/ICal/prompt/docs/authoritative/rfc5545.txt
[rfc5546]: ../../../Evals/ICal/prompt/docs/authoritative/rfc5546.txt
[rfc7529]: ../../../Evals/ICal/prompt/docs/authoritative/rfc7529.txt
[iges-116]: ../IGES-1.0.16.md
[iges-117]: ../IGES-1.0.17.md
[iges-tr]: ../../../Evals/IGES/prompt/technical-requirements-prompt.md
[iges-spec]: ../../../Evals/IGES/prompt/docs/iges-5-3-specification.md
