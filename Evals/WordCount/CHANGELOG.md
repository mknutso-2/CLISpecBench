# WordCount Changelog

## v1.0.3 — unreleased

### Changed

- **Container `python` symlink**: added `python-is-python3` to
  `docker/base.Dockerfile` so the bare `python` command resolves to
  `/usr/bin/python3` inside both agent and test containers. Matches the
  contract documented in `Evals/_shared/language-requirements-py.md`
  (`python main.py <arguments>`) which Ubuntu 24.04 otherwise breaks
  by shipping only `python3`. Test scoring is unaffected because
  `submission_command` already hard-resolves `/usr/bin/python3`.

## v1.0.2 — 2026-04-12

- **Prompt: non-interactive instruction**: appended shared
  `Evals/_shared/require-one-shot.md` to the assembled prompt, telling agents
  this is a non-interactive task — implement the full solution without asking
  questions or waiting for confirmation.

## v1.0.1

- Broadened exit-code 1 in `technical-requirements-prompt.md` to explicitly
  cover invalid invocations (missing/unknown arguments, missing input file)
  in addition to malformed input. Exit-code 2 is now reserved for unexpected
  internal failures (panic, OOM). Resolves an ambiguity that caused
  `test_missing_args_exit_code` to fail for an agent that reasonably
  classified missing-arg as an internal error.

## v1.0.0

Initial test suite.
