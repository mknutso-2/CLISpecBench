This repo stores the implementation for a new software engineering benchmark. To start, it contains code for only a single eval in the benchmark called CNCSim.

Contents:
- SWE-BuildBench-Design.md contains the proposed benchmark-level design.
- CNCSim/CNCSim-Design.md contains the CNCSim-specific eval design. This design doc mentions a full and lite version of the eval. We're currently working on just the full version.
- CNCSim/tests/ contains the CNCSim tests run against the implementation written during the eval (or on the "reference" implementation)
- CNCSim/prompt/base-prompt.md is the 'non-technical' prompt presented to the AI coding agent.
- CNCSim/prompt/technical-requirements-prompt.md is the 'technical' prompt presented to the AI coding agent for the sole purpose of documenting the requirements enforced by the testing harness. **You should update this document whenever new requirements are incurred by the testing harness. e.g. when new state variables are added to the output schema. Agents must be able to, theoretically, pass every test in the suite using only base-prompt.md, technical-requirements.prompt.md, and the docs/ folder.**
- CNCSim/prompt/docs/RS274NGC.md contains the RS274 documentation converted to markdown. **Do not edit files in this folder unless explicitly asked to do so.**
- CNCSim/reference-implementation/ contains a running reference implementation of the eval. At each commit, it should contain an implementation that passes all the tests in the eval.