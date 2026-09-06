# Regrading saved submissions

Run the current hidden tests against preserved source without another model call:

```bash
uv run clispecbench regrade transient_results/rs274-py/codex-cli/gpt-6-astra_low/eval1/run1/result.json --output-dir regrades/rs274-py-astra-low
```

The output directory must be new or empty and outside the original run directory.
The input must have its saved source and every referenced artifact available. A
published result JSON alone is insufficient; use its original transient run.
Docker is the default and uses a pinned immutable ID of `clispecbench-base`, with
the same build/test pipeline as a normal run. `--local` explicitly selects a host
diagnostic; its toolchain can differ from the benchmark container.

The command creates a distinct `regrade.json`, **not a new model `result.json`**.
It records:

- Original run UID, complete generation metadata (including the original eval,
  prompt, and test identifiers), original scores, and the original JSON SHA-256.
- A byte-identical `original-result.json`, a pristine `source/` snapshot, and a
  manifest/hash of every preserved file. Paths inside the raw original JSON still
  describe the original run, whose location is recorded in `regrade.json`.
- A snapshot of the exact new `tests/`, its manifest/hash, grading eval version,
  repository revision/dirty state, harness manifest/hash, timestamps, and grader
  environment. Docker grading records and uses the immutable image ID.
- The raw `test-report.json`, complete test outcomes, aggregate counts,
  correctness, and per-capability subscores computed by the standard scorer.

Builds/tests use a disposable source copy inside an `output/` directory, preserving
the agent workspace's package layout. The original source, source snapshot, model
result, token/cost accounting, and published dashboard records are not rewritten.
No files are excluded based on directory names: an authored module may live in
`build/`, or the submission may use vendored dependencies. The complete snapshot
and manifest preserve those inputs, including any existing generated files.
The ordinary build backend still chooses the build directory and command.
Source containing symlinks is rejected rather than silently following links
into another directory or altering their meaning across platforms.

A grader failure returns a nonzero command exit and saves an audit with
`grading.status = "failed"`, an explicit error, and null scores. A partial or
inconsistent test report is never converted into a valid zero or partial score.
Normal completed pytest failures still produce a valid regrade and a successful
command exit; inspect the reported pass count.

## Interpretation and publication

Compare results only after confirming their grading eval version, test hash,
grader environment, and unchanged source hash. A regrade says how **old source**
performs under the new rubric. It does not say the model saw the new prompt or
benefited from later clarifications. If a release changes both docs and tests,
report that generation/grading mismatch when presenting regrades; fresh model
trials are needed to measure performance with the new instructions.

Regrades are kept separate from ordinary run discovery and publication. The
`publish` command and dashboards are intentionally unchanged: do not rename a
regrade to `result.json`, overwrite generation metadata, or silently replace a
historical score. Present regrade comparisons with their provenance in an audit
report, and decide any official result migration explicitly.

## Cohort rules for any official migration

A regrade of one model is not a new benchmark result for that model. Promoting
regraded scores into the published record is a cohort-level operation, and these
rules constrain it:

- **No partial promotion.** Do not migrate one model's regrades into the
  published record while comparable models remain at an older grading version.
  A single migrated cohort scored under a corrected rubric, sitting beside
  cohorts scored under the rubric it corrected, manufactures a difference that
  no model earned. Either every cohort you intend to compare moves to the same
  grading version, or none does.
- **Match generation conditions, not just grading.** Cohort membership requires
  the same grading version, test hash and grader environment *and* comparable
  generation provenance. Check `metadata.network_policy` explicitly: saved runs
  with no policy marker are not interchangeable with `api-only` runs, and a
  label such as `<model>_<effort>` may cover several saved runs of which only
  one was published. Select by published run UID, never by score.
- **Do not select runs by score.** When a label has multiple saved runs, picking
  the best, the worst, or the first sorted by score biases the cohort. Resolve
  the intended run through its published UID.
- **State the grader image.** Regrades that used different Docker image IDs are
  not a shared grader, even at the same test hash. Record the image ID per
  cohort and say so when they differ.
- **The published record is not homogeneous.** RS274 rows already span more than
  one grading version. Do not assume the current dashboard is internally
  consistent; check `eval_version` per row before drawing any cross-model
  comparison from it.
