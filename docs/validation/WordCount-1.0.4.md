# WordCount 1.0.4 scoring audit — 2026-09-11

All model-visible prompt and documentation bytes remain unchanged. The suite
now has 46 cases. The public specification explicitly defines characters as
bytes, lines by LF, an exhaustive set of six whitespace delimiters, and the ten
highest word frequencies with lexicographic ties. New cases cover UTF-8 byte
counts, CRLF bytes, CR-only versus LF lines, non-delimiter Unicode spaces,
complete top-ten selection and cutoff ties, and combined case frequencies.

The schema tests reject booleans in integer fields and require a nonempty
example before checking frequency-entry structure. A punctuation case checks
decoded words containing quotes/backslashes, allowing any valid JSON escaping.
The unknown-argument case uses otherwise valid paths, so a missing-file error
cannot earn rejection credit. These checks exposed two C++ reference defects:
silently accepted unknown arguments and unescaped word strings in JSON. Both
reference defects are repaired under the same patch version.

The shared behavioral helper writes exact input bytes, clears stale output,
and reads actual output independently of successful-exit conformance. The
dedicated exit-code test retains that obligation. This avoids counting one
incorrect exit status as dozens of distinct counting failures.

## Validation

Pinned offline Docker grader:
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`.
All four reference implementations pass **46/46**. Repositories are mounted
read-only and references copied into disposable build directories. Raw reports
are retained in `work/non-rs274-audit/wordcount-final/` on the audit workstation.
Ruff and strict Pyright pass for the changed test directory. An independent
agent reviewed the final tests, C++ fixes, public-spec basis, version and date;
no actionable findings remained.

Mutation checks exercise codepoint counting, Unicode-default splitting,
arbitrary top-ten tail entries, and correct JSON with an incorrect process exit.
Each loses the named behavioral checks; the exit mutant loses only the
dedicated success-exit gate. This is targeted evidence of useful discrimination,
not a proof of exhaustive coverage. No old generated WordCount sources were
present locally, so reference/mutation checks are not historical model regrades.

## Public questions deferred

The corpus does not define a complete non-ASCII lowercasing/collation policy or
which byte encodings constitute malformed plain text. The new Unicode inputs
test only explicit byte and delimiter requirements. No unstated casing or
encoding-rejection convention is imposed retroactively.
