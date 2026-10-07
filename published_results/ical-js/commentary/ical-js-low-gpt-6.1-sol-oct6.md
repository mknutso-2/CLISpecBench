# GPT-6.1 Sol/low — ical-js

Run UID: `08f3adaf-1807-414f-be70-2e9e53649f15`.

The Node-builtins implementation completed voluntarily and passed 465/467 frozen tests. Reversed RDATE PERIOD and COUNT plus UNTIL deliberately throw InputError and exit 1, whereas the suite requires typed retention plus malformed_value warnings and exit 0. These are deterministic recovery-policy mismatches, not crashes or absent functionality; the public prompt does not expressly settle those two RFC-invalid cases. Unsupported-scale fallback and leap-second limits remain documented.

Frozen-suite limitation: retain ICal 3.0.5 and its observed score unchanged under docs/validation/non-rs274-2026-09-12/ical-valarm-publication-hold.md. Typed/raw duplication and unmodeled-parameter projection ambiguities, the LOCATION-TYPE fixture/citation issue, and invalid floating UNTIL in STANDARD must be distinguished from genuine semantic defects; no prompt/test repair or score adjustment is made here.

Accounting and network review: original token/cache/output fields and frozen-rate cost estimates are preserved; cached tokens are part of input and reasoning tokens are already included in output. These are API-equivalent estimates, not reported subscription charges. The API-only destination audit allowed only declared chatgpt.com API hosts; visible tools show no successful external fixture/reference-solution acquisition or hidden-suite access. Destination enforcement does not inspect encrypted TLS content, and canonical requested model/effort is not independent server-model attestation. Genuine capture truncations, source redaction exceptions and opaque reasoning are retained where present, not claimed fully readable.

Original generation result, frozen score, accounting and final-review evidence are unchanged. This publication adds an editorial summary and commentary only.
