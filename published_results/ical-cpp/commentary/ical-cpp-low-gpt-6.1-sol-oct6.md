# GPT-6.1 Sol/low — ical-cpp

Run UID: `4d4a096c-cd4e-4d33-aa01-b9bac58be696`.

The C++20 standard-library implementation completed voluntarily and passed 463/467 frozen ICal 3.0.5 tests. Two EXRULE failures wrongly remove DTSTART because the shared positive generator inserts the seed before BY filters. A reversed RDATE PERIOD lacks an ordering warning, and COUNT plus UNTIL exits 1 instead of the suite's warning-only recovery. The latter is a public invalid-input versus recovery-policy ambiguity, not an unambiguous RFC warning requirement. Astronomical precision limits are acknowledged.

Frozen-suite limitation: retain ICal 3.0.5 and its observed score unchanged under docs/validation/non-rs274-2026-09-12/ical-valarm-publication-hold.md. Typed/raw duplication and unmodeled-parameter projection ambiguities, the LOCATION-TYPE fixture/citation issue, and invalid floating UNTIL in STANDARD must be distinguished from genuine semantic defects; no prompt/test repair or score adjustment is made here.

Accounting and network review: original token/cache/output fields and frozen-rate cost estimates are preserved; cached tokens are part of input and reasoning tokens are already included in output. These are API-equivalent estimates, not reported subscription charges. The API-only destination audit allowed only declared chatgpt.com API hosts; visible tools show no successful external fixture/reference-solution acquisition or hidden-suite access. Destination enforcement does not inspect encrypted TLS content, and canonical requested model/effort is not independent server-model attestation. Genuine capture truncations, source redaction exceptions and opaque reasoning are retained where present, not claimed fully readable.

Original generation result, frozen score, accounting and final-review evidence are unchanged. This publication adds an editorial summary and commentary only.
