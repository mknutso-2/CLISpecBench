# Tar

POSIX.1-2008 `pax` archive format eval for CLISpecBench — agents receive the pax utility spec and must produce a CLI tool that lists, extracts, and creates tar archives in ustar and PAX interchange formats.

> **Status.** Proposed eval shell. This README is a design sketch — no prompt, tests, or reference implementation yet.

## Why this eval

Tar is a natural candidate on paper: the archive format is a dense, fixed-layout 512-byte-block binary spec with well-defined extensions (ustar, PAX extended headers, GNU `@LongLink`), strong determinism (given an archive, listing and extraction have one correct result), and a sizable surface of edge cases (checksum sign conventions, numeric base-256 extensions, sparse file maps, zero-block termination). The POSIX.1-2008 `pax` utility specification is the single authoritative source of the interchange format and is freely published by The Open Group.

However, tar is one of the highest-contamination file formats in existence. "Build Your Own Tar" is a canonical teaching exercise (John Crickett's Coding Challenges #54), `microtar` and friends are popular drop-in single-file reference implementations, and every major language has a polished standard-library tar module (Python `tarfile`, Go `archive/tar`, Rust `tar`). An agent can almost certainly recite the ustar header layout from memory. The interesting question this eval would ask is whether the agent can get the *corners* right — corners that published minimal implementations routinely skip.

RS274 (dense spec, low contamination) and IGES (dense spec, almost no contamination) are this benchmark's spec-comprehension workhorses. Tar, if included, would play a different role: a "low spec density, high trap density" eval measuring whether an agent can navigate a format it already knows cursorily without falling into the well-documented pitfalls.

See the **Risks and Open Questions** section for why this is a hard sell.

## Documentation Corpus

Primary source: **POSIX.1-2008 `pax` utility specification** (IEEE Std 1003.1-2008 / The Open Group Base Specifications Issue 7), published at [pubs.opengroup.org/onlinepubs/9699919799/utilities/pax.html](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/pax.html). This single page defines:

- The `pax` interchange archive format (section "pax Interchange Format"), including the extended header keyword/value grammar `%d %s=%s\n`.
- The legacy `ustar` header layout, field widths, and numeric encoding rules.
- The 12 typeflag values (regular file, hardlink, symlink, char/block device, directory, FIFO, contiguous, `g`/`x` extended headers, and the reserved vendor-extension range).
- Interchange rules (what readers must accept, what writers must produce, encoding of long names, hardlink resolution semantics).

The spec is stable and self-contained, but **redistribution is not automatic**: the Open Group publishes POSIX/IEEE Std 1003.1-2017 openly online for reading, with copyright held by The Open Group and IEEE; hosting a verbatim mirror under `prompt/docs/` would need either written permission or a transcribed/paraphrased summary (RS274-style). See "Risks and Open Questions" and the `Publicly distributable docs` line on the checklist — this is partial, not pass. The spec also does not cover GNU-specific extensions (`././@LongLink`, GNU sparse 0.0/0.1/1.0), which is a design choice discussed below.

**Supporting corpus candidates** (all public, but selection would need care to avoid shipping solver code):

- A small normative prose summary of ustar numeric encoding corners (base-8 with NUL/space terminators; base-256 signed high-bit extension for files >8 GiB).
- A short appendix describing GNU `@LongLink` *only* to the extent needed to read legacy archives (not to write them). The eval would explicitly require writing PAX extended headers, not GNU long-link blocks.

No tutorials, worked code, or reference implementations in the prompt corpus.

## Base Prompt (sketch)

> I manage long-term archival storage for a small research institute. Most of what comes across my desk is tar files — decades of lab data, instrument dumps, third-party deliverables, backups from retired Unix boxes. Some are modern pax archives, some are older ustar archives, and some are from ancient GNU tars with their own quirks. I need a single tool I can run on any of these archives to do three jobs reliably.
>
> First, I need to **list** the contents of an archive: every entry with its name, size, type (file, directory, symlink, hardlink, character/block device, FIFO), modification time, owner and group (by name where the archive records them, by numeric ID otherwise), and permissions. Long filenames and linknames — the kind that don't fit in the 100-character header field — need to be reconstructed from whichever extension mechanism the archive uses, whether that's a modern PAX extended header or a legacy GNU `@LongLink` marker. The listing must be a stable, structured format I can diff against old listings.
>
> Second, I need to **extract** the archive's entries into a target directory. File contents must match byte-for-byte, permissions must be preserved, and the header checksum must be verified before an entry is trusted. Entries whose names would escape the target directory (absolute paths, `..` components) must be refused with a clear error and a nonzero exit. Hardlinks should be reported in the listing as pointing to their target, but do not need to be materialized on disk — recording the relationship in the output is enough.
>
> Third, I need to **create** a new archive from a directory tree. The output should be a well-formed PAX interchange archive: ustar where the values fit in the base fields, PAX extended headers where they don't (long names, long linknames, high-precision times, large sizes). The end of the archive must be correctly terminated with two zero-filled 512-byte blocks.
>
> The tool must not care whether the input archive is gzip- or xz-compressed; that's someone else's job. It works on uncompressed tar streams only. It doesn't need to run the tar protocol over a network, it doesn't need to talk to a tape drive, and it doesn't need to handle GNU sparse files beyond *recognizing* that they exist and reporting them in a listing.

## Technical Requirements (sketch)

CLI contract (single binary, default name `tar`, exit 0 on success, 1 on invalid input, 2 on internal error). Three subcommands:

| Subcommand | Purpose |
|---|---|
| `tar list --input <archive.tar> --output <listing.json>` | Emit a structured listing of every entry with resolved names and metadata |
| `tar extract --input <archive.tar> --target <dir> --output <report.json>` | Extract entries; report bytes-written per entry, checksum-pass/fail, refusals |
| `tar create --source <dir> --output <archive.tar> --report <report.json>` | Pack a directory tree into a PAX interchange archive; report entries written and format used per entry |

All JSON output uses canonical keys defined in `technical-requirements-prompt.md`. Listings are ordered by archive position (not sorted) so tests can assert positional semantics. Extension mechanism used per entry (`ustar`, `pax`, `gnu-longlink`) is reported explicitly.

Format scope:

- **Must read**: ustar, PAX interchange (POSIX.1-2001), GNU `@LongLink` long-name and long-link markers.
- **Must write**: PAX interchange format (writer falls back to plain ustar only when all fields fit without extensions).
- **Must recognize but not reconstruct**: GNU sparse 0.0/0.1/1.0 (report as `sparse` in listing, skip data in extract with a `skipped=true` entry).
- **Out of scope**: Compression (gzip/bzip2/xz), network/tape I/O, hardlink materialization, `star` extensions, binary cpio.

## Test Suite Estimate

| Category | Est. tests |
|---|---|
| Ustar header parsing (all 12 typeflags, field-width boundaries, NUL vs space terminators) | ~15 |
| Checksum verification (correct, corrupted, unsigned-vs-signed ambiguity, all-space initial state) | ~6 |
| Numeric encoding (octal with trailing NUL, octal with trailing space, base-256 for size > 8 GiB, negative mtime) | ~8 |
| PAX extended header parsing (length-prefix grammar, multi-record headers, `path`, `linkpath`, `size`, `mtime`, `atime`, `uid`, `gid`, `uname`, `gname`, global `g` vs local `x`) | ~12 |
| GNU `@LongLink` legacy reading (`L` long name, `K` long linkname, interaction with following real header) | ~5 |
| Zero-block termination (exactly two zero blocks, more than two, truncated at one, trailing garbage) | ~5 |
| Directory structure and typeflags (directories with trailing slash, symlinks, hardlinks, FIFOs, devices, contiguous) | ~8 |
| Path-safety refusals in `extract` (absolute path, `..`, symlinked-parent traversal, null-byte injection) | ~6 |
| Name/prefix splitting (ustar 155+100 split rules, edge cases at the boundary) | ~5 |
| PAX writer format selection (fallback-to-ustar when fits, PAX when doesn't, large-size promotion) | ~8 |
| Round-trip fidelity (create then list then extract preserves metadata) | ~6 |
| GNU sparse recognition (0.0, 0.1, 1.0 variants reported correctly, skipped in extract) | ~4 |
| Malformed-archive diagnostics (bad checksum, truncated header, unrecognized typeflag, bad PAX length prefix) | ~8 |
| **Total** | **~96** |

Each category admits independent failure modes; a single "forgot NUL-terminator on names" bug fails the name-reading tests but not the checksum or PAX-parsing tests.

## Implementation Size Estimate

Grounded reference points:

- **CPython `Lib/tarfile.py`**: ~2,250–2,300 SLOC (varies by version; 2,582 physical lines in Python 3.9, ~2,253 SLOC per GitHub's sloc counter). This is the closest apples-to-apples reference for "read+write ustar+PAX+GNU extensions, no compression driver" — Python's implementation does handle compression but the compression layers are thin wrappers around stdlib modules; the core tar logic is the bulk of that number.
- **Go `archive/tar`**: implementation split across `common.go`, `format.go`, `reader.go`, `writer.go`, `strconv.go` plus two tiny stat shims. The whole package is in the low four digits of lines total.
- **`microtar`** (rxi/microtar, MIT): a *minimal* drop-in C implementation in `microtar.c` + `microtar.h`. Substantially smaller than the above but also substantially less compliant — it does not handle PAX extended headers, long names via PAX, GNU `@LongLink`, sparse recognition, base-256, or most of what the eval would test.

CLISpecBench requires roughly 1000 LOC minimum for a competent reference implementation. A submission that implements everything in the test matrix above — ustar reader, PAX reader with keyword parsing, GNU `@LongLink` reader, PAX-first writer with ustar fallback, path-safety extraction — would plausibly land in the **~1,500–2,500 LOC** range in C++ or Python. Comfortably above the floor.

## Contamination & OSS Landscape

**Specific implementations found:**

- [GNU tar](https://savannah.gnu.org/git/?group=tar) — C, maintained since 1990, the canonical reference. Full feature set including GNU sparse formats, PAX, ustar, and deep tape/network support. Open Hub's COCOMO estimate puts effort at roughly 7 person-years, implying low five-digit LOC across the whole project.
- [libarchive](https://github.com/libarchive/libarchive) — C, "multi-format archive and compression library." Its tar reader and extract-to-disk routines compiled to ~260 KiB on FreeBSD in 2009; source is a few thousand LOC across `archive_read_support_format_tar.c` and friends, carefully factored.
- [CPython `tarfile`](https://github.com/python/cpython/blob/main/Lib/tarfile.py) — Python, ~2,253 SLOC. Handles ustar, PAX, GNU-tar including long names and sparse. Stdlib.
- [Go `archive/tar`](https://go.dev/src/archive/tar/) — Go, low four-digit LOC across `common.go`, `format.go`, `reader.go`, `writer.go`, `strconv.go`. Stdlib.
- [alexcrichton/tar-rs](https://github.com/alexcrichton/tar-rs) — Rust, 108M+ downloads on crates.io. The de-facto Rust tar crate.
- [astral-sh/tokio-tar](https://github.com/astral-sh/tokio-tar) — async Rust fork of tar-rs.
- [uutils/tar](https://github.com/uutils/tar) — Rust reimplementation of the tar *utility* (CLI). Part of the Coreutils-in-Rust effort.
- [rxi/microtar](https://github.com/rxi/microtar) — C, MIT, designed for drop-in use. ustar only, no PAX, no long-name support. Popular as a teaching reference.
- [brunexgeek/minitar](https://github.com/brunexgeek/minitar), [calccrypto/tar](https://github.com/calccrypto/tar), [marprok/tar-tools](https://github.com/marprok/tar-tools), [Keruspe/tar-parser.rs](https://github.com/Keruspe/tar-parser.rs), [mafintosh/tar-stream](https://github.com/mafintosh/tar-stream) — a long tail of MIT/BSD "I wrote a tar parser" personal projects, collectively covering every mainstream language.

**Tutorials / walkthroughs:**

- [Coding Challenges #54: Build Your Own Tar](https://codingchallenges.fyi/challenges/challenge-tar/) — John Crickett's well-known teaching exercise. Walks through ustar parsing and creation explicitly as a learning exercise. Directly adjacent to this eval's scope.
- [Thomas Lovén: TAR Filesystem](http://thomasloven.com/blog/2014/01/TAR-filesystem/) — implementation walkthrough with code.
- [Building a fast tar replacement in Rust (riptar)](https://alxhill.dev/topics/riptar.html) — implementation post.
- [copyprogramming.com: How to parse a tar file in C++](https://copyprogramming.com/howto/how-to-parse-a-tar-file-in-c) — code-first tutorial.
- GNU tar's own [manual chapter on Basic Tar Format](https://www.gnu.org/software/tar/manual/html_node/Standard.html) — authoritative prose walkthrough of the 512-byte header, field-by-field.
- Wikipedia's [tar (computing)](https://en.wikipedia.org/wiki/Tar_(computing)) article — comprehensive header-format reference including field offsets and widths, prominently indexed.

**Contamination risk: HIGH.** Essentially every frontier model has seen (a) the ustar header layout at least dozens of times, (b) one or more "write a tar parser" tutorials verbatim, (c) the full source of Python's `tarfile`, Go's `archive/tar`, Rust's `tar`, and GNU tar, and (d) the coding-challenge walkthrough. The public prompt corpus on this task cannot plausibly introduce any ustar or PAX behavior the model has not already memorized.

## Risks and Open Questions

**The central concern is contamination.** Tar is to file formats what linked lists are to data structures: every student implements one at some point, every language's stdlib ships one, every "build your own X" curriculum includes it. An agent asked to implement tar is overwhelmingly likely to be recalling patterns rather than reasoning about the spec. This is exactly the failure mode `CHOOSING_EVALS.md` calls out under "Contamination resistance," and it is the dominant objection to this eval existing at all.

There is a *compensating* argument, which is that the published implementations — especially the short/popular ones — routinely get the corners wrong:

- `microtar` and most "learning tar" projects skip PAX extended headers entirely and cap names at 100 characters.
- The unsigned-vs-signed checksum ambiguity (GNU uses unsigned, SunOS/HP-UX historically used signed; both are acceptable per the spec) is frequently overlooked.
- The base-256 signed numeric extension for files > 8 GiB is omitted from nearly every minimal implementation.
- GNU's `././@LongLink` convention is not in POSIX and is often missed by readers that claim PAX support.
- Two-zero-block termination is sometimes collapsed into "any zero block" or "EOF equals end," both of which silently lose trailing entries.
- G92-style "suspend the offset without writing back" transitions (RS274) have a moral equivalent here in the PAX `g`-record (global extended header) that applies cumulatively to every following entry until overridden — readers that treat `g` records as local frequently produce wrong listings on multi-entry global-header archives.

A well-authored eval could emphasize these corners in the test suite. That would plausibly re-introduce signal — an agent that recalls "tar is 512-byte blocks with an octal header" but cannot navigate the PAX `g` vs `x` distinction, or treats the checksum as always-unsigned, would fail a substantial fraction of the suite. But: the test signal then comes almost entirely from the contamination-resistant corners, and an eval that *must* concentrate on corners to avoid triviality is a fragile eval. Better candidates exist.

**Specific open questions, assuming the eval is pursued:**

1. **Scope: ustar only, or include PAX and GNU?** A ustar-only eval is simpler but has almost no contamination resistance — ustar fits in a page and every model has implemented it. Including PAX raises signal but also raises author burden (PAX grammar tests must be carefully constructed to be unambiguous).
2. **Include create, or read-only?** A read-only eval (list + extract) is a cleaner scoring surface because the output is a structured listing and a set of extracted files; creation introduces "is there more than one valid byte-for-byte output?" questions (PAX header field ordering, optional fields, choice of atime/mtime precision). The proposal above includes create; reconsidering as "read-only, plus creation folded into roundtrip tests only" would tighten the scoring surface.
3. **Publicly distributable docs.** The POSIX pax spec is published by The Open Group but their licensing of re-hosted copies is not as permissive as, say, IEEE's RS274 NGC document. A transcribed summary may be necessary rather than a verbatim mirror. This is a CHOOSING_EVALS checklist item that would need real legal review before the eval ships.
4. **GNU sparse.** Three incompatible versions (0.0, 0.1, 1.0), each with its own quirks, and all three are GNU extensions outside POSIX. Including read-support for sparse raises the ceiling substantially but also drags the eval into a domain where the "spec" is really just the GNU manual. Current proposal: recognize and report, do not reconstruct.
5. **Path-safety behavior.** Extraction's refusal rules (absolute paths, `..`, symlink-aware parent traversal) are not fully specified by POSIX — POSIX says a conformant extractor "should" strip leading `/`. Different tars do different things. This pushes requirements out of the spec and into the harness contract, which is a warning sign per the CHOOSING_EVALS checklist.

## CHOOSING_EVALS Checklist

- **Documentation-first: partial.** POSIX `pax` spec covers ustar and PAX cleanly, but GNU `@LongLink` and GNU sparse recognition require supplementary prose in the corpus, and path-safety behavior for `extract` is not authoritatively specified anywhere. The eval would end up with a mixed corpus: one authoritative spec plus eval-author prose. That mirror is not disqualifying (IGES has supporting prose) but is weaker than RS274's single-document model.
- **Non-developer describable: pass.** The sysadmin/data-curator persona is natural and the base prompt above is written in that voice without engineering guidance.
- **Authoritative source material: pass for ustar/PAX, partial for GNU extensions.** POSIX.1-2008 is the authoritative spec for the interchange format. GNU extensions are documented only in the GNU tar manual, which is authoritative-for-GNU but not standards-track.
- **No solver code in corpus: pass.** The POSIX spec is prose and grammar, not code. Supplementary prose would be author-written. `microtar`, `tarfile.py`, etc. would never ship in the corpus.
- **Behaviorally unambiguous: partial/fail.** Several behaviors the test suite would want to assert (path-safety rules, PAX writer's exact choice of when to promote a field to an extended header, handling of duplicate PAX keywords, global-header scoping) are underspecified in POSIX and differ across implementations. Each of these requires a harness-contract ruling. A test suite built on "we pick the Python-tarfile behavior" is weaker than one built on the spec.
- **Deterministic scoring surface: partial.** Listings are deterministic. Extract is deterministic for file contents and metadata. Create is *not* deterministic byte-for-byte in PAX (field ordering, optional records) — would have to score create via roundtrip rather than byte-equality, which is what the test table above does.
- **Independent failure modes: pass.** The test categories in the table are largely orthogonal: a checksum bug fails checksum tests but not name-parsing, a PAX-grammar bug fails PAX tests but not ustar, etc.
- **System-level complexity: pass.** Reader, writer, header codec, PAX keyword parser, path-safety layer, typeflag dispatch, and two extension-format handlers (PAX, GNU `@LongLink`) is a real multi-module system, comfortably past the 1000-LOC floor.
- **Test-suite scalability: pass.** ~96 tests sketched above, all independent-behavior, with plausible headroom to 150+ via adversarial corpora and edge-case permutations.
- **Contamination resistance: FAIL.** See the Risks section. This is the deciding criterion against the eval.
- **Reference implementation feasibility: pass.** Straightforward; the eval author can build a compliant reference on a weekend or two, or lightly adapt an existing permissively-licensed implementation (careful to keep it out of the prompt corpus).
- **Reasonable harness fit: pass.** Local files, CLI flags, structured JSON output, no network, no GUI. Fits the model exactly.
- **Publicly distributable docs: partial.** The Open Group publishes the pax spec openly, but redistribution terms are less permissive than the RS274 NGC document's public-domain status. A transcribed summary is likely required; a verbatim mirror probably is not.

## Summary

Tar is a good-looking eval concept that runs into a wall on the contamination criterion. The format is authoritative, publicly specified, system-level, cleanly scorable through a CLI, and admits a test suite well past the 50-test floor — every criterion except contamination is a pass. But ustar and PAX are in the training data of every frontier model dozens of times over, published in every language's stdlib, and taught as a named "Build Your Own Tar" coding challenge. A test suite that concentrates on the corners (checksum sign, base-256, `@LongLink`, PAX `g`-scoping, two-block termination) could claw back some signal, but the eval then derives its difficulty from a narrow ring of traps rather than from genuine spec comprehension. **Recommendation: do not build this eval unless a future contamination audit of frontier models shows surprising weakness on the edge cases above.** RS274 and IGES already cover the dense-spec-comprehension track with better contamination profiles.
