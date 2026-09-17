# IGES 1.0.18 Logical writer fixture repair — 2026-09-17

Final test suite SHA-256:
`18d38836c2f1efe04557fdbf276d3cebc4c7a367ac0e82d6249c7ee4c7c78eda`.
The suite retains **261 cases** and all four assembled model inputs are
unchanged. No reference implementation or generated source is modified.

## Invalid prerequisite and retained observation

The Astra JavaScript generation `97909084-fe80-42ff-b359-2a30798f8f67`
originally scored 259/261 under 1.0.17. One failure was a real acceptance of
illegal zero-count Hollerith. The other was an invalid positive fixture in
`test_logical_values_in_parameter_records_use_zero_and_one`: its Face510 had
`surf=0`, `n=0` and no loops or Shell parent. The implementation correctly
rejected it before the test observed any boolean output.

Public §4.146 requires an underlying surface, one or more loops (explicitly
`N > 0`), and a Shell parent. The test now uses the previously independently
validated `open_triangle_document`: 13 records with a real plane, closed
oriented boundary, Face and independent open Shell. It inspects only the
Face's outer-loop flag in physical Parameter data. It never invokes the
submitted parser or geometry evaluator. Both flag values are legal: false
means no loop is designated as outer (§4.146).

The Logical rule is public §2.2.2.6 and technical requirements' non-FieldValue
boolean serialization clause. Unsigned integer 1/0 is required when explicit;
implicit FALSE remains permitted by §§2.2.2.6/2.2.3. The observation tolerates
integer padding, DE renumbering, split physical records, and post-terminator
comments. It does not compare unrelated support fields. This is one repaired
false negative, not removal of the independently valid Hollerith test.

## Validation and independent review

All execution used offline Docker image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`,
read-only repository mounts and disposable reference copies, sequentially.
Python, C++ and JavaScript references each pass the full 261-case suite.
After the final owner-ID formatting tolerance adjustment, the focused test
was rerun against all three references and passed at the final hash above.

Three disposable Python reference mutations emit text booleans, real-number
booleans, or reversed truth values. Each fails at the intended Logical token
assertion. A control emitting `01` for true and an empty defaulted field for
false passes. The topology validator accepts the 13-record triangular context.
Ruff formatting/checks and strict Pyright pass.

Independent reviewer `resume_single_review` confirmed the invalid original
prerequisite, public truth-value/defaulting rules, final test scope and version
discipline. Its owner-ID padding observation was incorporated. Reference and
control summaries and unchanged-input hashes are retained in
`IGES-1.0.18-checks.json`; full local evidence is in
`work/non-rs274-audit/iges-1.0.18-validation/`.

## Saved submissions and limits

Original source, transcripts, usage and generation grades remain immutable.
Fresh-source regrades under the committed rubric are published separately in
`regraded_results/iges/1.0.18/gpt-6-astra_max/` with original-result/source
hashes, exact grading provenance and complete prior publication payloads.
All ran sequentially under the pinned image, with no new generation calls.

| Astra Max submission | 1.0.17 score | 1.0.18 score | Change |
|---|---:|---:|---|
| Python | 261/261 | 261/261 | All outcomes unchanged |
| C++ | 259/261 | 259/261 | All outcomes unchanged |
| JavaScript | 259/261 | 260/261 | Only repaired Logical fixture changes to pass |

JavaScript still incorrectly accepts `0H`. C++ both accepts and writes `0H`;
those are separate reader/writer observations of one shared rule error.
Python passes both. Its older generation score of 170/260 and previous
regrade history also remain preserved. The JavaScript generation used 41
tool calls, 23,051 reasoning tokens and a recorded $8.583752 API-equivalent
estimate; none of that accounting changed during regrading.

The legal topology remains a prerequisite to observing its writer field;
the test cannot eliminate every dependency of a valid IGES file. It avoids
the previously invalid graph and any submitted parse/eval dependency. The
public ambiguities and deferred analytic-offset cases documented for 1.0.17
remain unchanged; a perfect score is not exhaustive IGES conformance.
