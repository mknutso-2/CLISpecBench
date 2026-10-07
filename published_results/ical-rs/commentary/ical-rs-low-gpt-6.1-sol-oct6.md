# GPT-6.1 Sol/low — ical-rs

Run UID: `6feff408-ecbd-490d-92ef-0cf3054626a9`.

The Rust standard-library implementation completed voluntarily and passed 462/467 frozen tests. Two EXRULE failures remove selector-unmatched DTSTART via unconditional seed inclusion. Reversed PERIOD and COUNT plus UNTIL terminate instead of the frozen warning-only policy; preserve that ambiguity. The remaining floating UNTIL in STANDARD is the documented RFC-invalid positive fixture: rejecting it does not prove broken valid UTC cutoff handling. Final 27 checks comprise 24 unit and three CLI tests.

Frozen-suite limitation: retain ICal 3.0.5 and its observed score unchanged under docs/validation/non-rs274-2026-09-12/ical-valarm-publication-hold.md. Typed/raw duplication and unmodeled-parameter projection ambiguities, the LOCATION-TYPE fixture/citation issue, and invalid floating UNTIL in STANDARD must be distinguished from genuine semantic defects; no prompt/test repair or score adjustment is made here.

Accounting and network review: original token/cache/output fields and frozen-rate cost estimates are preserved; cached tokens are part of input and reasoning tokens are already included in output. These are API-equivalent estimates, not reported subscription charges. The API-only destination audit allowed only declared chatgpt.com API hosts; visible tools show no successful external fixture/reference-solution acquisition or hidden-suite access. Destination enforcement does not inspect encrypted TLS content, and canonical requested model/effort is not independent server-model attestation. Genuine capture truncations, source redaction exceptions and opaque reasoning are retained where present, not claimed fully readable.

Original generation result, frozen score, accounting and final-review evidence are unchanged. This publication adds an editorial summary and commentary only.
