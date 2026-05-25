# Contributing to CLISpecBench

Contributions are welcome, especially fixes to the harness, documentation,
published-results tooling, agent adapters, and eval clarity.

## Development workflow

Before opening a pull request, run the checks that match your change:

```bash
bash scripts/ci-lint.sh
bash scripts/ci-unit.sh
```

For eval-specific changes, also run the relevant eval tests where possible:

```bash
pytest Evals/<Task>/tests --language=<lang>
```

Some tests require Docker, local toolchains, or agent credentials. If you cannot
run a relevant check locally, say that clearly in the pull request.

## Eval changes

Changes to eval prompts, docs, tests, reference implementations, or versioning
must follow the repo instructions in `AGENTS.md`.

In particular:

- Hidden tests are intentionally part of the benchmark design.
- Prompt/docs/test changes may require updating the eval `VERSION` and
  `CHANGELOG.md`.
- Reference implementations should continue to pass the eval tests for their
  language.
- Do not edit mirrored specification material under `Evals/*/prompt/docs/`
  unless the change is intentional and documented.

## Pull requests

Please include:

- A concise description of the behavioral change.
- The commands you ran.
- Any checks you could not run and why.
- For result-publication changes, enough context to audit why the result should
  be included or excluded.

## License

By contributing to this repository, you agree that your contributions are
licensed under the Apache License 2.0 unless explicitly stated otherwise.
