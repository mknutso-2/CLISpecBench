# GPT-6.1 Sol/low — ical-py

Run UID: `519aa7a5-b1db-4355-b5fa-ce2bd7cc5e4c`.

The Python standard-library implementation completed voluntarily and passed 464/467 frozen tests. Two invalid-value cases (reversed RDATE PERIOD and COUNT plus UNTIL) terminate with exit 1 where the suite expects warning-only recovery; retain the public invalid-input/recovery-policy caveat. The third is a genuine pre-first-observance timezone defect: a horizon-bounded empty transition list returns unchanged wall time but appends Z, producing 10:00Z instead of 15:00Z for the 1995 example. Unsupported astronomical calendars are acknowledged, not silently claimed implemented.

Frozen-suite limitation: retain ICal 3.0.5 and its observed score unchanged under docs/validation/non-rs274-2026-09-12/ical-valarm-publication-hold.md. Typed/raw duplication and unmodeled-parameter projection ambiguities, the LOCATION-TYPE fixture/citation issue, and invalid floating UNTIL in STANDARD must be distinguished from genuine semantic defects; no prompt/test repair or score adjustment is made here.

Accounting and network review: original token/cache/output fields and frozen-rate cost estimates are preserved; cached tokens are part of input and reasoning tokens are already included in output. These are API-equivalent estimates, not reported subscription charges. The API-only destination audit allowed only declared chatgpt.com API hosts; visible tools show no successful external fixture/reference-solution acquisition or hidden-suite access. Destination enforcement does not inspect encrypted TLS content, and canonical requested model/effort is not independent server-model attestation. Genuine capture truncations, source redaction exceptions and opaque reasoning are retained where present, not claimed fully readable.

Original generation result, frozen score, accounting and final-review evidence are unchanged. This publication adds an editorial summary and commentary only.
