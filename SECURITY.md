# Security Policy

Please do not report security issues publicly.

If you find a vulnerability involving CLISpecBench, especially anything related
to credential handling, Docker sandboxing, agent execution, or published
artifacts, report it privately using GitHub's private vulnerability reporting or
by contacting the repository maintainer directly.

## Scope

Security-sensitive areas include:

- Agent credential mounting and host credential discovery.
- Docker sandbox setup and filesystem mounts.
- Scripts that execute agent CLIs or generated submissions.
- Published artifacts that could accidentally expose secrets or private paths.

## Non-security issues

General bugs, flaky tests, documentation issues, and benchmark-design questions
can be reported with normal GitHub issues.
