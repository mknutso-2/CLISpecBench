# SAM

Sequence Alignment/Map (SAM) v1.6 text-format parser and query eval for CLISpecBench. Agents receive the SAM 1.6 specification and must produce a CLI tool that parses SAM records, decodes CIGAR strings and flag bitmasks, resolves optional tags, reconstructs reference sequence from the MD tag, and answers region queries against a sorted SAM file.

> **Status.** Proposed eval shell. This README is a design sketch — no prompt, tests, or reference implementation yet.

## Why this eval

RS274 and IGES both test dense-spec comprehension in mechanical-domain file formats. SAM broadens the benchmark into life sciences, where the spec is similarly dense but the behavioral surface is quite different: bitmask flag decoding, run-length CIGAR operations, type-tagged optional fields, and a cross-field reference reconstruction (CIGAR + MD + SEQ). It is a natural third eval because:

- **The spec is short, dense, and authoritative.** SAM v1.6 is roughly 25 pages of formal grammar, flag tables, and type codes — a single self-contained document analogous to RS274/NGC.
- **Independent failure modes.** Flag decoding, CIGAR parsing, MD reconstruction, optional-tag typing, and region querying are mostly orthogonal. A bug in one rarely cascades into all tests passing or all tests failing.
- **Adversarial edge cases.** CIGAR semantics for clipping (S vs. H), padding (P), and the rarely-used `=`/`X` operators; MD-tag interaction with insertions and deletions; strand sense in flag bit 0x10; secondary (0x100) vs. supplementary (0x800) vs. duplicate (0x400) distinctions all have well-documented subtleties that even production tools get wrong.
- **Non-developer describable.** A bioinformatics analyst can naturally describe "I want to inspect aligned reads in a region and see what each one matched" without resorting to software engineering vocabulary.

Text SAM only — the gzipped binary BAM variant is explicitly out of scope (see Non-Goals).

## Documentation Corpus

Single primary document plus one small companion:

- **`SAMv1.pdf`** (v1.6, samtools group, hosted at https://samtools.github.io/hts-specs/SAMv1.pdf). The authoritative specification. Covers record layout, CIGAR grammar, flag semantics, header lines (@HD/@SQ/@RG/@PG/@CO), optional-field typing, sorting, indexing, and validation rules. Maintained in the samtools/hts-specs GitHub repository as `SAMv1.tex`; the PDF is regenerated from that source.
- **`SAMtags.pdf`** (companion "Optional Fields Specification"). Documents standardized tag names (MD, NM, RG, etc.) with their type codes and semantics. Needed because the MD-tag reconstruction requirement is defined here, not in SAMv1.pdf.

Both documents are authored by the samtools maintainers as open GA4GH-aligned specifications and distributed from a public GitHub repository. The repository does not ship an explicit LICENSE file for the specification text itself, but the specifications are published for implementation, routinely redistributed in textbooks and course materials, and cross-referenced from the GA4GH standards page. We should confirm redistribution rights before shipping copies in the repo; if there is any doubt, the corpus can instead link to a pinned commit hash on the hts-specs repo and bundle our own transcribed markdown (as RS274 does with `RS274NGC.md`) to sidestep the question entirely.

## Base Prompt (sketch)

_Written in a bioinformatics-analyst voice — no developer jargon:_

> I work with short-read DNA sequencing output and I spend a lot of time eyeballing SAM files to figure out what my aligner did with a given read — whether it mapped to the forward or reverse strand, whether it's flagged as a duplicate, where exactly the soft-clipped portion starts, whether the MD tag agrees with what the CIGAR says. Right now I mostly use `samtools view` piped through `awk`, but I'd like a cleaner tool that emits structured output I can drop into a notebook.
>
> I want a command-line tool that reads a text SAM file and emits JSON. Given a region like `chr1:10000-20000`, it should print every alignment that overlaps, one JSON object per record. Each record should have the 11 mandatory fields decoded (flag bits broken out as a named object, CIGAR expanded to a list of `{op, len}` pairs, optional tags typed by their code), plus a reconstructed reference sequence derived from the CIGAR, the MD tag, and the read sequence. The tool should also answer a few focused questions: "list all read groups in this file," "how many primary alignments are in this region," "what's the reference sequence for this one record." The SAM 1.6 specification defines all of this.

The prompt would not prescribe a file layout, a language, a library, or an algorithm. It would lean on the spec for the hard behavioral requirements.

## Technical Requirements (sketch)

- **Language.** Single reference implementation in Python first (for ecosystem familiarity), with the CLI contract language-agnostic so Rust, C++, Go ports are viable.
- **CLI.** Single binary with subcommands, following the RS274/IGES convention (exit 0 on success, 1 on invalid input, 2 on internal error; all output is JSON):
  - `sam parse --input <file.sam> --output <out.jsonl>` — emit one JSON object per alignment record.
  - `sam query --input <file.sam> --region <chr:start-end> --output <out.jsonl>` — filter to overlapping records. (Linear scan is acceptable; no .bai index required.)
  - `sam header --input <file.sam> --output <out.json>` — emit decoded header as structured JSON.
  - `sam reconstruct --input <file.sam> --qname <read-id> [--hit <n>] --output <out.json>` — emit reconstructed reference for a single alignment.
  - `sam flag --decode <integer>` — standalone flag decoder (print bit breakdown as JSON).
- **Output schema.** Canonical per-record JSON with:
  - All 11 mandatory fields named (QNAME, FLAG, RNAME, POS, MAPQ, CIGAR, RNEXT, PNEXT, TLEN, SEQ, QUAL).
  - `flags`: named object with boolean fields for the 12 defined bits.
  - `cigar`: list of `{op, len}` pairs.
  - `tags`: map from tag name to `{type, value}` where `type` is the one-character SAM code (A, i, f, Z, H, B) and arrays carry their element type.
  - `reference`: reconstructed reference sequence string, present iff an MD tag is present.
- **Scope limits.** Text SAM only; no BAM; no alignment algorithms; no index files; no CRAM; no MACRO-style extensions.

## Test Suite Estimate

| Category | Est. tests |
|---|---|
| Header parsing (@HD version, @SQ sort/length, @RG, @PG, @CO) | ~10 |
| Mandatory-field parsing (11 fields, `*` sentinels, type coercion) | ~8 |
| Flag bitmask decoding (12 bits, named outputs, edge values) | ~8 |
| CIGAR parsing (M/I/D/N/S/H/P/=/X, long runs, empty/star CIGARs, malformed) | ~12 |
| Optional tags (A/i/f/Z/H, B arrays with all subtypes, duplicate tags) | ~10 |
| MD-tag reference reconstruction (matches, substitutions, deletions, interaction with CIGAR I/S/H) | ~12 |
| Region query (overlap edge cases, empty result, across-chromosome, malformed region) | ~8 |
| Sorted-vs-unsorted behavior (@HD SO field respected) | ~3 |
| Malformed-input handling (truncated records, bad tag type, out-of-range flag, exit 1 + diagnostic) | ~8 |
| Strand/mate-pair semantics (flags 0x10/0x20/0x40/0x80 interactions, proper-pair 0x2) | ~6 |
| Secondary vs. supplementary vs. duplicate (0x100 / 0x800 / 0x400) | ~5 |
| CLI contract (exit codes, JSON schema stability, empty-file handling) | ~5 |
| **Total** | **~95** |

Comfortably clears the 50-test floor from CHOOSING_EVALS.

## Implementation Size Estimate

Target implementation is ~1200–1800 LOC in Python, distributed roughly:

- ~300 LOC header + record tokenizer and mandatory-field parser.
- ~200 LOC CIGAR parser + expander.
- ~100 LOC flag decoder.
- ~250 LOC optional-tag parser (every type code including B arrays).
- ~300 LOC MD-tag reconstruction (non-trivial — see Risks).
- ~150 LOC region query (linear scan with interval overlap).
- ~200 LOC CLI wiring + JSON serialization + error paths.

Reference sanity-check:

- `simplesam` (mdshw5/simplesam) is ~500 LOC pure Python but is a much thinner parser — no MD reconstruction, no region query, minimal flag helpers.
- `noodles-sam` (Rust, part of zaeleus/noodles) is substantially larger but handles indexing, BGZF, and a BAM companion crate we explicitly exclude.
- `pysam` and `htsjdk` wrap htslib (C) and are primarily bindings; not directly comparable.

The 1200–1800 target clears the ~1000 LOC floor in CHOOSING_EVALS while staying under RS274's scope.

## Contamination & OSS Landscape

**Specific implementations found:**

- [samtools](https://github.com/samtools/samtools) — C, the canonical reference. A large, production toolkit: parsing, sorting, indexing, pileup, mpileup, region query, flagstat, and hundreds of other commands. Far broader in scope than this eval.
- [htslib](https://github.com/samtools/htslib) — C, the library behind samtools, pysam, htsjdk-jbr and others. Handles SAM/BAM/CRAM/VCF/BCF and their indices. Implements every corner of SAM v1.6 and then some.
- [pysam](https://github.com/pysam-developers/pysam) — Python, thin wrapper over htslib. Its user-facing surface is what most educational material points at.
- [htsjdk](https://github.com/samtools/htsjdk) — Java, the Broad Institute's implementation used by GATK and Picard. A large codebase ([`SAMUtils.java`](https://github.com/samtools/htsjdk/blob/master/src/main/java/htsjdk/samtools/SAMUtils.java) alone is a substantial file).
- [noodles-sam](https://github.com/zaeleus/noodles) — Rust, pure-Rust (no htslib binding). Part of `zaeleus/noodles`. Explicitly claims SAM 1.6 conformance.
- [biogo/hts](https://github.com/biogo/hts) — Go, pure-Go SAM/BAM implementation. Published JOSS paper (doi:10.21105/joss.00168).
- [simplesam](https://github.com/mdshw5/simplesam) — Python, intentionally minimal single-file parser (~500 LOC). Closest in scope to what this eval asks for, but lacks MD reconstruction and region query.
- [sam2pairwise](https://github.com/mlafave/sam2pairwise) — C++, small utility specifically for CIGAR+MD pairwise reconstruction. Highly relevant to one of this eval's hardest requirements.
- [rust-htslib](https://github.com/rust-bio/rust-htslib) — Rust, htslib binding (not a reimplementation).

**Tutorials / walkthroughs:**

- [JEFworks — "CIGAR Strings For Dummies"](https://jef.works/blog/2017/03/28/CIGAR-strings-for-dummies/) — introductory walkthrough.
- [Tim Dunn — "CIGAR Strings"](https://timd.one/blog/genomics/cigar.php) — detailed reference.
- [Broad Picard — "Explain SAM Flags"](https://broadinstitute.github.io/picard/explain-flags.html) — the canonical flag decoder.
- [Dave Tang — "Understanding the BAM flags"](https://davetang.org/muse/2014/03/06/understanding-bam-flags/) — interprets each bit with examples.
- [Genome Analysis Wiki — SAM](https://genome.sph.umich.edu/wiki/SAM) — textbook-style explainer.
- [mlell — "Parsing of SAM files"](https://mlell.github.io/tapas/06_sam-parsing.html) — step-by-step parser tutorial.
- [Heng Li — "The history the MD tag and the CIGAR X operator"](https://lh3.github.io/2018/03/27/the-history-the-cigar-x-operator-and-the-md-tag) — from the spec's primary author, explicitly on the subtleties.
- Harvard STAT115, various university bioinformatics courses — SAM is a standard topic in every short-read-sequencing curriculum.

**Contamination risk: medium-high.** Unlike RS274 and IGES, SAM is genuinely ubiquitous in the training corpus: it is covered in every bioinformatics introductory course, has multiple production implementations spanning five languages, and has dozens of tutorial walkthroughs written by domain experts. A strong agent has almost certainly seen SAM parser code and CIGAR explanations during training.

The saving grace is that the *edge cases* separate recall from understanding:

- Correct MD-tag reference reconstruction with interleaved CIGAR insertions is a common source of bugs even in mature libraries — the Heng Li blog post is explicitly about how hard this is.
- The `=`/`X` and `P` CIGAR operators are rare in real data; most implementations get them subtly wrong or ignore them.
- The secondary (0x100) vs. supplementary (0x800) vs. duplicate (0x400) distinction is widely misunderstood; hts-specs issue #445 documents community confusion about it.
- The G-style strand/mate-pair flag interactions (particularly bit 0x20's dependency on 0x1) are a known source of errors.

A thoughtfully adversarial test suite can push hard on these corners to differentiate "memorized a SAM tutorial" from "actually read the SAM 1.6 spec."

## Risks and Open Questions

- **Contamination ceiling.** Even with adversarial edge cases, a very strong agent with deep bioinformatics training data may saturate this eval quickly. Worth estimating the ceiling before investing in a full test suite. If preliminary runs show current frontier models at 95%+, the eval is too easy to serve as a differentiator.
- **License clarity.** hts-specs does not publish an explicit LICENSE file for the specification documents. Before shipping `SAMv1.pdf` or a transcribed markdown copy, confirm redistribution terms (the samtools maintainers are reachable; worst case, we transcribe our own summary from the public LaTeX source, as RS274 does).
- **MD reconstruction subtlety.** MD-tag reconstruction interacts with CIGAR in ways the SAM 1.6 spec describes correctly but concisely. Some real-world aligners emit MD tags that disagree with the spec under insertion/clipping combinations. Reference implementation must decide whether to be strict (reject) or permissive (warn + produce best-effort output); the prompt must make this choice explicit.
- **Rare CIGAR operators.** `P` (padding) and `=`/`X` (explicit match/mismatch) are underused in practice. Including them gives the eval discriminating power but also risks testing behavior the spec itself is terse about. Treat these as mandatory coverage but with carefully bounded test cases.
- **Region-query semantics.** SAM v1.6 defines the on-disk layout but not CLI query semantics; the "overlap" rule has to be specified in `technical-requirements-prompt.md` rather than the public spec. This is the pattern IGES/RS274 also use for harness-contract behavior; worth flagging as a contract requirement rather than a spec requirement.
- **Sorted-file dependency.** Linear scan is fine for the eval (small files), but the spec documents `@HD SO:coordinate` / `SO:queryname`. We should decide: do we require the agent to honor sort order in `query` output, or just overlap-filter and preserve input order?
- **Test corpus ownership.** Unlike RS274 (no public fixtures exist) and IGES (ships `ex1`/`ex2`/`ex3`), SAM has a massive public fixture ecosystem (1000 Genomes, Tabula Muris, samtools' `test/` directory). We should generate our own synthetic fixtures rather than bundle public ones, both to sidestep licensing and to keep test inputs minimal.

## CHOOSING_EVALS Checklist

- **Documentation-first: pass** — SAMv1.pdf + SAMtags.pdf are self-contained authoritative specs; every testable behavior is defined there.
- **Non-developer describable: pass** — a bioinformatics analyst can naturally describe inspection and region-query use cases without developer vocabulary.
- **Authoritative source material: pass** — samtools/hts-specs is the canonical source, maintained by the spec's original authors and endorsed by GA4GH.
- **No solver code in corpus: pass** — SAMv1.pdf and SAMtags.pdf are specifications, not worked implementations. The public corpus never includes a reference parser.
- **Behaviorally unambiguous: partial** — most of the spec is unambiguous, but a few areas (MD tag behavior under unusual CIGAR combinations, `P` operator adjacency rules) require careful eval-author clarification in `technical-requirements-prompt.md`.
- **Deterministic scoring surface: pass** — JSON-per-record output is fully deterministic; comparison is straightforward.
- **Independent failure modes: pass** — flag / CIGAR / MD / tag / region categories are largely orthogonal; a bug in one does not cascade.
- **System-level complexity: pass** — 1200–1800 LOC spanning tokenization, multiple parsers, reference reconstruction, region indexing, and CLI. Not a one-file script.
- **Test-suite scalability: pass** — ~95 tests estimated; the behavior surface supports more if needed (e.g., additional standardized tags from SAMtags.pdf).
- **Contamination resistance: partial (lean toward fail)** — this is the biggest concern. SAM is heavily covered in training data with multiple polished OSS implementations in five languages and dozens of tutorials. Edge-case testing helps but does not eliminate the risk. Mark this as the primary gating question before committing to the eval.
- **Reference implementation feasibility: pass** — straightforward to build a Python reference implementation from the spec; `sam2pairwise` and `simplesam` demonstrate individual pieces are tractable.
- **Reasonable harness fit: pass** — pure-local CLI, no network, no GUI, no hosted services, no concurrency. Fits RS274/IGES pattern exactly.
- **Publicly distributable docs: partial** — redistribution rights for SAMv1.pdf need confirmation; fallback is to transcribe from the public LaTeX source (hts-specs is a public GitHub repo).

## Summary

SAM 1.6 is a natural third CLISpecBench eval: a short, dense, authoritative specification whose behavioral surface decomposes cleanly into orthogonal sub-tasks (flag decoding, CIGAR parsing, MD-tag reconstruction, optional-tag typing, region query) with plenty of adversarial edge cases and a comfortable 1200–1800 LOC reference target. The chief risk is contamination: SAM is taught everywhere and re-implemented in at least five production OSS libraries, so a strong agent has almost certainly seen parser code during training. That risk is real but not fatal — the edge cases around MD reconstruction, rare CIGAR operators, and flag-bit interactions are well-documented sources of bugs even in mature tools, and a carefully adversarial test suite can plausibly differentiate recall from comprehension. Before committing, we should (1) confirm specification redistribution rights, (2) estimate the contamination ceiling with a small pilot test suite against current frontier models, and (3) decide whether to transcribe our own markdown copy of the spec (IGES-style) or ship the original PDF.
