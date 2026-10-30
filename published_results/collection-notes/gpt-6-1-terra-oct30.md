# GPT-6.1 Terra reviewed-results publication — October 30, 2026

This publication adds 96 reviewed GPT-6.1 Terra attempts collected on October 29, 2026: all eight evals × four languages × low, high and max effort, one run per cell.

Runs used Codex CLI 0.165.0 (the first version with a Terra catalog entry) under the API-only network condition, with hosted web search and apps disabled, on harness 0.2.2 and a ChatGPT Pro subscription. Each attempt has a final review of its result, complete final message, failed tests, session model (only `gpt-6.1-terra` in every run), commands and network audit. Per-eval commentary files (`gpt-6.1-terra-publication-oct30-2026.md`) list each run's failures, network attempts and review notes.

## Effort levels behave very differently

At max, Terra worked 10–25 minutes per cell and scored at or near the top on most evals, including 2900/2900 MARC21 and 223/223 LAS in every language. At high and low it stopped after roughly 0.5–3 minutes on every eval, and in 50 of 64 runs its final message says the implementation is incomplete; those are published as Incomplete. No infrastructure cause was found: these are completed, model-side runs.

## Disclosures

- Under the API-only proxy, many runs tried to install tools or fetch references (rustfmt, clang-format, a reference BibTeX via apt/pip/npm, sample CAD files from GitHub, Unicode or calendar tables). Every such request was denied and nothing was retrieved; each attempt is listed in the run's commentary entry.
- IGES JS max scored 227/249, and 20 of its 22 failures come from argument order: the IGES 1.0.21 contract says `--output` is the final flag, but the hidden-suite helper passes `--s` after `--output`, and this submission enforces the documented order. IGES 1.0.22 fixes the helper; under it this source regrades to 247/249. The published score stays at the graded 227 unless a regrade promotion is approved. The high and low IGES JS runs accept either order and regrade unchanged (178 and 153).
- Some network audits contain an egress-proxy traceback from a reset connection, not an audit event; it does not affect the run.

## Accounting

Dollar amounts are API-equivalent estimates from token counts at Terra's standard rates ($1 input, $0.05 cached input, $5 output per million tokens): about $26.60 for max and $5.74 for high and low. They are not charges; runs drew on the operator's subscription and used about 9% of its weekly allowance. No prompt, test, score or token counter was changed for publication; raw sessions and operational logs stay local.
