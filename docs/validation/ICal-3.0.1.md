# ICal 3.0.1 validation — 2026-09-11

All model-visible prompt/docs bytes are unchanged. The fixes follow the public
corpus's explicit authority hierarchy and do not introduce new public behavior.

## Findings and repairs

**Spring-gap UTC conversion.** The base prompt says that the RFCs govern when
the summary disagrees; the summary opening repeats that hierarchy. RFC 5545
§3.3.5 (`rfc5545.txt`, around line 1896) says a nonexistent explicit local time
uses the UTC offset **before** the gap. The summary's §5.1.1 instead calls the
post-transition interpretation mandatory. The old hidden test and C++ reference
followed the lower-authority summary. The corrected test requires 07:30Z for
2026-03-08 02:30 America/New_York, not 06:30Z. The reference applies the pre-gap
offset, including non-hour jumps. While making that fix, validation also found
that one-off DTSTART/RDATE candidates after the queried local time were treated
as active; filtering future candidates restores the explicitly documented
pre-first-observance TZOFFSETFROM fallback. Focused half-hour-gap and
before-one-off-observance cases protect those behaviors.

An exploratory test accepted both described offsets. Independent review caught
that this ignored the explicit public authority hierarchy; that approach was
removed before the final rubric. The conflicting summary prose should still
be corrected in a separate public-input revision, but it does not override the
RFC under the existing contract.

**Unknown TZID policy.** Summary §5.1.2 explicitly states:

> Implementations MAY alternatively treat unresolved TZID as a hard parse error;
> that MUST be clearly documented on the tool's `--help` output if so.

The two behavior cases previously forced continuation. They now accept a
structured rejection, or require the documented warning, floating timestamp,
and original TZID for continuation. One case uses a familiar IANA name without
an in-file definition, checking the §12 prohibition on host timezone lookup.
The policy's free-prose `--help` documentation requires human review; no
arbitrary phrase matcher or unrelated help precondition is inserted into these
behavior tests. A structured error remains necessary, so a bare crash receives
no credit.

**Line folding.** RFC 5545 §3.1 recommends that producers fold physical lines
above 75 octets. Neither it nor the supplied summary defines a mandatory
reader `line_too_long` trigger/prohibition. Three line-length cases now check
exact decoded DESCRIPTION content at 75 octets, over the limit, and after
folding. Empty JSON can no longer pass a warning-absence case. Warning presence
is optional until the public custom-warning behavior is explicitly clarified.

**False recurrence credit and duplicate gates.** Gregorian leap-year and SKIP
cases now compare complete date lists, rejecting extra incorrect occurrences.
When Chinese/Hebrew support is claimed, tests require all five dates explicitly
listed in RFC 7529 §§4.3.1/4.3.3; returning the original Hebrew DTSTART alone
previously passed. The existing unsupported-calendar warning/raw-RRULE fallback
is retained. Duplicate top-level key tests now check independent value types,
and expand permits extension keys consistently with parse. DST warning-absence cases additionally require the input event to be observed,
so empty JSON does not earn credit. Response files are removed before each invocation.

## Validation and limits

The C++ reference passes **467/467** in offline Docker image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`,
with the repository mounted read-only and a disposable build. Ruff and strict
Pyright pass for changed Python tests. Test-suite hash:
`c697367b53202f1da674d915e86e279f48b4c551816ef5a0cb196f17167f30f7`.

A controlled wrapper claims Hebrew recurrence support, removes the unsupported
warning, and emits only the initial 2014-02-08 occurrence. The original Hebrew
case passes; the repaired case fails. Thus the stronger check distinguishes
actual sequence computation from an unchanged anchor. Full reference passing
is not evidence of exhaustive RFC coverage or reliable ranking at the ceiling.

The non-Gregorian fallback's exact scope is inadequately spelled out in the
public prose: the schema names `rscale_unsupported`, while historical tests and
changelog permit fallback even for Gregorian SKIP. A future public revision
should explicitly state supported calendars and fallback behavior. This patch
does not silently remove that established acceptance path when fairly scoring
old source. No saved historical model sources were present on this machine, so
this report makes no claim of new historical model regrades.
