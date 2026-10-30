# Claude 5.5 reviewed-results publication — October 30, 2026

This publication adds the reviewed Sonnet 5.5 and Opus 5.5 attempts collected from October 13 to 29, 2026, filling the high and max cells that the [October 13 publication](claude-5-5-oct13.md) left open:

- Sonnet 5.5: high on the seven non-RS274 evals (28 runs) and max on all eight evals except the already-published RS274 JS cell (31 runs), plus one rerun.
- Opus 5.5: high on the seven non-RS274 evals (28 runs) and max on all eight evals (32 runs), plus five reruns.

Runs used Claude Code 2.1.289 under the web-enabled condition, one run per cell, on a long-lived subscription token. Each published attempt has a final review of its result, complete agent claims, failed tests, stream/native/`modelUsage` models, tool use, subagents and network commands. Per-run editorial summaries compare the agent's claims with its outcome; a completed run is not necessarily a fully conforming implementation. Per-eval commentary files (`claude-5-5-publication-oct30-2026.md`) list each run's failures, network use and review notes.

## Harness versions

Results stamp `metadata.harness_version`; see the repository `CHANGELOG.md`.

- 0.1.0 (63 runs) and 0.2.0 (13): before and after headless wake-up tools were blocked.
- 0.2.1 (31): Claude Code's web-tool helper model follows the run's model instead of Haiku 4.5.
- 0.2.2 (18): the CLI refusal fallback is disabled, so a flagged request cannot move the run to another model.

Sonnet BibTeX C++ max is published with harness_version 0.1.0: it ran under 0.1.0 conditions and was stamped 0.2.0 only because the package was bumped while it was finishing.

## Reruns and incomplete runs

Six cells ended in a way the reviews flagged and were rerun once at the end of the collection; both attempts are kept where publishable:

- Background-subagent stops (Sonnet IGES Rust max; Opus GEDCOM JS, MARC21 JS, WordCount JS and WordCount Python max): the agent ended its turn while a background subagent was still running, and the headless CLI stopped it, so promised follow-up work never happened. The first attempts are published as Incomplete beside their reruns.
- Refusal fallback (Opus IGES Rust max): the CLI silently retried a flagged request on `claude-opus-4-8` and stayed there for part of the run. That attempt is not published; its 0.2.2 rerun is.

Four RS274 max runs (Sonnet C++; Opus JS, Python and Rust) are published as Output cap: each ended on a single response over the model's own per-response maximum before writing source, a model-side outcome that is counted and not rerun.

## Exclusions

- Sonnet IGES C++ max: cross-model sidecar requests (the pre-0.2.1 Haiku helper) make it ineligible for pure-model publication.
- Opus IGES Rust max, first attempt: refusal-fallback model mix (above).

That leaves 123 published Claude attempts.

## Network and accounting

Agents could use the network under the web-enabled condition. Each run's commentary entry records what it fetched or installed (for example pymarc, MARC-Lint, GEDCOM sample files, rustup components), or that it used none.

Dollar amounts are CLI-reported API-equivalent figures (about $2,333 across the 125 attempts), not charges: runs drew on the operator's subscription, with extra usage disabled. No prompt, test, score, token counter or historical result was changed for publication; raw transcripts and operational logs stay local.
