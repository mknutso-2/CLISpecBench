# BibTeX reference fixtures

The eight expected BBLs are independently generated from the two test corpora
and the four byte-identical public reference styles. They are observations
of the supplied public specification, not a separate hidden contract.

The 2026-09-12 regeneration used Ubuntu's `texlive-binaries`
`2023.20230311.66589-9build3`, whose executable reports
`BibTeX 0.99d (TeX Live 2023/Debian)`. Package, executable, corpus,
style, citation-list, and output SHA-256 values are recorded in
`oracle-provenance.json`. The executable and its library were extracted into
scratch; no repository reference implementation generated these outputs.

The public prose names BibTeX 0.99c, but the shipped authoritative
`bibtex.web` declares 0.99e. Its version history states that 0.99e changes only
program typesetting and has no functional changes from 0.99d. The 0.99d oracle
therefore implements the supplied WEB behavior. This version discrepancy is
a public-documentation clarification for a later public-input revision.

Regeneration must explicitly set `max_print_line=79` (WEB's public limit);
an isolated TeX Live binary without its configuration otherwise defaults to
a different line length. Set `min_print_line=3` and retain the documented
`min_crossrefs=2` default. Generate an AUX with the supplied style, database,
and each key from the corresponding `.cites` file in order. Run BibTeX in a
fresh directory containing only those inputs, require exit 0, and preserve
the produced BBL bytes. Do not seed goldens from a submission or reference.

Both corpora place formerly inherited fields directly in the children and
remove their `crossref` fields. This prevents one cross-reference threshold
bug from failing all eight style cases; direct tests retain that coverage.
Names use one token per name part so the permitted always-space approximation
and faithful WEB inter-token ties produce the same parity output. Multipart
name behavior remains covered by dedicated name tests.
The edge corpus spells raw Gödel as `G{\"o}del` to avoid a byte/codepoint
ambiguity in alpha labels; dedicated Unicode cases retain UTF-8 coverage.
Empty booktitle and journal warnings are
expected for that corpus; they do not prevent successful output. Both
corpora pass the independent oracle for all four styles.

The corrected outputs fix previously reference-derived punctuation, name
inter-token ties, and cross-reference retention/inheritance. Direct tests
separately localize these behaviors; a reference-style mismatch alone can
still represent several shared prerequisites and is not a count of
independent bugs. The public bounded accent rules continue to apply.
