# IGES Changelog

## v1.0.0 — unreleased

Initial release (in progress). Scaffolding only — the eval is not yet
functional. See `PLAN.md` for port status.

### Added

- `Evals/IGES/` directory with `README.md` and `PLAN.md`.
- `VERSION` = `1.0.0`, this `CHANGELOG.md`.
- `iges` task registered in `src/swe_buildbench/harness/task.py`
  `_KNOWN_TASKS` (pointing at `Evals/IGES`, language `cpp`). The task
  will not actually run end-to-end until the prompt, tests, and
  reference implementation land.
