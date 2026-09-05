# RS274 Deferred Changes

This file records proposed contract changes that have been investigated but
have not yet been applied. Entries here are not part of the agent-visible eval
contract. Implement each entry only with the corresponding `VERSION` and
`CHANGELOG.md` update.

## Accept unterminated programs at end of file

**Status:** Proposed for the next RS274 contract bump. Do not include results
produced before and after this change in the same result series.

### Problem

`prompt/docs/RS274NGC.md` section 3.2 says that percent delimiters are required
when a file has no M2 or M30 and that omitting both is an error. The current
test suite, reference implementations, and trace examples instead treat many
short, undelimited snippets without M2/M30 as successful programs. The
technical requirements also say that documented specification errors must
exit 1 while presenting successful examples such as `G1 X1 F60` that end at
EOF without a program-end command.

This contradiction can reward implementations that ignore the supplied
specification and heavily penalize implementations that follow it. It is not
merely theoretical: GPT-5.6 Terra high and max C++ both implemented the
documented M2/M30-or-percent requirement.

Recorded results on RS274 v3.2.0:

| Run | Official result | Diagnostic with only the EOF rejection disabled |
| --- | ---: | ---: |
| GPT-5.6 Terra high C++ | 261/546 (47.80%) | 442/546 (80.95%) |
| GPT-5.6 Terra max C++ | 266/546 (48.72%) | 484/546 (88.64%) |

The diagnostic scores are investigative evidence, not replacement benchmark
results: they were produced from manually modified copies of the submissions.

### Proposed normative rule

Add the following behavior to `prompt/docs/Clarifications.md`:

> For this non-interactive command-line simulator, reaching end of file after
> successfully executing all available blocks is a successful end of input,
> even when the file is not delimited by percent lines and contains no M2 or
> M30. End of file alone does not apply the modal, spindle, coolant, override,
> coordinate-system, or parameter reset effects of M2/M30. An opening percent
> delimiter still requires a closing percent delimiter, and explicit M2/M30
> retains all program-end and trailing-line behavior defined elsewhere.

This deliberately overrides the file-demarcation requirement in RS274 section
3.2 while preserving the observable distinction between plain EOF and an
explicit M2/M30 program end.

### Work to perform with the version bump

1. Add the normative rule to `prompt/docs/Clarifications.md`.
2. Add focused tests for successful plain-EOF termination and for the absence
   of M2/M30 reset effects at plain EOF. Retain coverage for unmatched percent
   delimiters and explicit M2/M30 behavior.
3. Confirm all four reference implementations follow the clarified behavior.
4. Bump the RS274 patch version and add a dated changelog entry describing the
   contract clarification and its motivation.
5. Run the complete reference-implementation test matrix, lint, and type
   checks required by the eval-authoring workflow.
6. Start a new result series under the new eval version. Keep RS274 v3.2.0
   results as historical data rather than combining them with corrected runs.
