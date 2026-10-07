# GPT-6.1 Sol/high — ical-rs

Run UID: `801f8f46-9488-48ac-abe6-340b580ebebe`.

The Rust implementation completed voluntarily and passed 463/467 frozen tests. Two EXRULE failures delete unmatched DTSTART. Reversed RDATE PERIOD retains syntactically valid endpoints without ordering warnings; COUNT plus UNTIL intentionally propagates an error to exit 1 instead of the frozen nonfatal policy. The latter is an RFC-invalid-input recovery-policy ambiguity, not proof that RFC requires warnings. Final 29-test/release checks are supported; bounded Chinese calendar data (1900-2100) is acknowledged.

Frozen-suite limitation: retain ICal 3.0.5 and its observed score unchanged under docs/validation/non-rs274-2026-09-12/ical-valarm-publication-hold.md. Typed/raw duplication and unmodeled-parameter projection ambiguities, the LOCATION-TYPE fixture/citation issue, and invalid floating UNTIL in STANDARD must be distinguished from genuine semantic defects; no prompt/test repair or score adjustment is made here.

Accounting and network review: original token/cache/output fields and frozen-rate cost estimates are preserved; cached tokens are part of input and reasoning tokens are already included in output. These are API-equivalent estimates, not reported subscription charges. The API-only destination audit allowed only declared chatgpt.com API hosts; visible tools show no successful external fixture/reference-solution acquisition or hidden-suite access. Destination enforcement does not inspect encrypted TLS content, and canonical requested model/effort is not independent server-model attestation. Genuine capture truncations, source redaction exceptions and opaque reasoning are retained where present, not claimed fully readable.

Original generation result, frozen score, accounting and final-review evidence are unchanged. This publication adds an editorial summary and commentary only.
