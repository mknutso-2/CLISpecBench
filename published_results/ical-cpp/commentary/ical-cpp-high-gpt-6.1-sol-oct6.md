# GPT-6.1 Sol/high — ical-cpp

Run UID: `e36d6b30-8423-4983-a993-b583cac2a867`.

The C++20 standard-library implementation completed voluntarily and passed 464/467 frozen tests. Two failures reuse unconditional positive DTSTART inclusion for EXRULE, incorrectly deleting nonmatching seeds. The third loses the earliest TZOFFSETFROM when all observance seeds lie beyond its request horizon, leaving a 1995 event unresolved rather than converting it to 15:00Z. These three are genuine implementation edge cases, separate from known projection/invalid-UNTIL caveats. Authored CTest and sanitizer successes are supported; they do not assert hidden-suite perfection.

Frozen-suite limitation: retain ICal 3.0.5 and its observed score unchanged under docs/validation/non-rs274-2026-09-12/ical-valarm-publication-hold.md. Typed/raw duplication and unmodeled-parameter projection ambiguities, the LOCATION-TYPE fixture/citation issue, and invalid floating UNTIL in STANDARD must be distinguished from genuine semantic defects; no prompt/test repair or score adjustment is made here.

Accounting and network review: original token/cache/output fields and frozen-rate cost estimates are preserved; cached tokens are part of input and reasoning tokens are already included in output. These are API-equivalent estimates, not reported subscription charges. The API-only destination audit allowed only declared chatgpt.com API hosts; visible tools show no successful external fixture/reference-solution acquisition or hidden-suite access. Destination enforcement does not inspect encrypted TLS content, and canonical requested model/effort is not independent server-model attestation. Genuine capture truncations, source redaction exceptions and opaque reasoning are retained where present, not claimed fully readable.

Original generation result, frozen score, accounting and final-review evidence are unchanged. This publication adds an editorial summary and commentary only.
