# BibTeX — Navigation Summary

> **This document is a navigation index, not the authoritative spec.**
> The authoritative sources are Oren Patashnik's original BibTeX
> documentation and source, shipped verbatim under
> [`authoritative/`](authoritative/):
>
> - [`authoritative/btxdoc.tex`](authoritative/btxdoc.tex) — *BIBTEXing*
>   — user-facing guide (`.bib` format, entry types, author-name
>   rules, `crossref`, `@string`, `@preamble`).
> - [`authoritative/btxhak.tex`](authoritative/btxhak.tex) —
>   *Designing BibTeX Styles* — `.bst` stack language, all built-in
>   functions, entry/global scope, sort, reverse-iterate, output
>   buffer rules (79-column line-wrapping), name-formatting grammar.
> - [`authoritative/bibtex.web`](authoritative/bibtex.web) — the
>   complete BibTeX 0.99c implementation (literate Pascal / WEB) — the
>   ultimate authority on stack discipline, string-buffer sizes,
>   error recovery, built-in semantics.
> - [`authoritative/plain.bst`](authoritative/plain.bst),
>   [`alpha.bst`](authoritative/alpha.bst),
>   [`unsrt.bst`](authoritative/unsrt.bst),
>   [`abbrv.bst`](authoritative/abbrv.bst) — the four reference styles
>   shipped with BibTeX. These are exercised by the end-to-end parity
>   tests: a correct `.bst` interpreter, fed these styles against a
>   reference `.bib`, must produce the same `.bbl` that BibTeX 0.99c
>   itself produces (byte-exact modulo the documented approximations
>   in §8 below).
>
> **Where this summary and the authoritative sources conflict, the
> authoritative sources are authoritative.** Tests in this eval assert
> behavior that is unambiguously specified by the sources above; this
> summary exists to help an implementer orient faster, not to replace
> or reinterpret them.

This document summarizes BibTeX 0.99c: the `.bib` database format,
the author-name grammar, the `.bst` style-file stack language, and
the `.bbl` output file it produces. A correct implementation reads a
`.bib` database and a `.bst` style file, executes the style's
stack-based program against the cited subset of entries, and
produces a `.bbl` output file byte-comparable to what BibTeX 0.99c
would produce.

## 1. `.bib` file structure

A `.bib` file is a sequence of *entries*. An entry is one of:

- A **regular entry**: `@TYPE{ key, field = value, ... }`
- A **`@string` entry** defining a macro: `@string{ NAME = value }`
- A **`@preamble` entry** declaring a TeX preamble: `@preamble{ value }`
- A **`@comment` entry**.

Text outside entries is ignored.

### 1.1 Tokenization

Entry types, field names, and the `@string` / `@preamble` / `@comment`
keywords are case-insensitive. Citation keys are case-sensitive and
preserved verbatim. Whitespace separates tokens but is otherwise
insignificant at the top level.

### 1.2 Entry delimiters

Entries may be delimited either by `{ ... }` or by `( ... )`. Both are
accepted; the opening character chooses the matching close.

### 1.3 Entry types

Standard entry types: `article`, `book`, `booklet`, `inbook`,
`incollection`, `inproceedings`, `conference`, `manual`,
`mastersthesis`, `misc`, `phdthesis`, `proceedings`, `techreport`,
`unpublished`. Entry types are normalized to lowercase in the output.

Unknown entry types are accepted; whether they produce output is a
style-file decision (the style's `call.type$` will branch to
`default.type` for unrecognized types).

### 1.4 Field values

A field value is a `#`-concatenated sequence of operands, where each
operand is:

- **Number**: a bare sequence of digits, e.g. `2024`. Concatenated as
  its decimal string form.
- **Braced string**: `{ ... }` with balanced braces inside. Outer
  braces stripped.
- **Quoted string**: `" ... "`. Outer quotes stripped.
- **Macro reference**: a bare identifier (not all-digits) referring
  to a previously-defined `@string` macro or a predefined month macro.

After `#`-concatenation, field values retain their internal whitespace;
BibTeX's whitespace-normalization happens only when a value is used
by the `.bst` language.

### 1.5 Predefined macros

Twelve month abbreviations are predefined:

| Macro | Expansion |
|---|---|
| `jan` | `January` |
| `feb` | `February` |
| `mar` | `March` |
| `apr` | `April` |
| `may` | `May` |
| `jun` | `June` |
| `jul` | `July` |
| `aug` | `August` |
| `sep` | `September` |
| `oct` | `October` |
| `nov` | `November` |
| `dec` | `December` |

User `@string` macros override these by same-name redefinition.

### 1.6 Crossref inheritance

When an entry has a `crossref` field whose value (case-insensitive)
matches another entry's key, the child inherits every field of the
parent that the child does not itself define. Inherited fields come
*after* the child's own fields in declaration order.

Cross-reference chains are *not* followed transitively. An unresolved
crossref is preserved in the child's output and emits a warning.

## 2. Author-name grammar

The `author` and `editor` fields (and any other field the `.bst`
style parses with `format.name$`) contain a list of one or more names
separated by the word `and` (case-insensitive, word-bounded).

Each name decomposes into four parts: **First**, **von**, **Last**,
**Jr**. The decomposition depends on comma count.

### 2.1 Tokens and case

A token is a maximal run of non-whitespace characters, except a brace
group `{ ... }` counts as a single token. A tie character `~` is a
TeX non-breaking space and separates tokens while being preserved
in literal form.

A token is "lowercase" if its first non-brace non-special character
is a lowercase letter. Tokens beginning with `{` are opaque and
treated as uppercase. Tokens beginning with `{\` (a TeX special
character) are also uppercase unless the first alphabetic character
inside the special is explicitly lowercase.

### 2.2 Form 1 — no commas (`First von Last`)

- `von` is the contiguous run of lowercase tokens from the first
  lowercase token through the last lowercase token.
- `Last` is everything *after* the last lowercase token, or if the
  name ends on a lowercase token, `Last` absorbs the trailing run
  and `von` is emptied (ensuring Last is non-empty).
- `First` is everything *before* the first lowercase token.
- If there are no lowercase tokens, `First` is all tokens except
  the last; `Last` is the single last token.
- `Jr` is empty.

### 2.3 Form 2 — one comma (`head, First`)

The text after the comma is `First`. The head is split into
`von` + `Last`:

- Leading uppercase tokens before the first lowercase → prepend to
  `Last`.
- Middle run of lowercase tokens → `von`.
- Trailing uppercase tokens after the last lowercase → `Last`.
- If the head has no lowercase tokens, the head is all `Last`.

### 2.4 Form 3 — two commas (`head, Jr, First`)

- Middle segment → `Jr`.
- Last segment → `First`.
- Head split as in Form 2.

### 2.5 Three or more commas

Only the first two commas are structural. Everything after the second
comma is joined with commas preserved into `First`.

## 3. `.bst` style file language

A `.bst` file is a program for a stack machine that consumes a
cited subset of the `.bib` database and produces a `.bbl` output file.
This section specifies the language.

### 3.1 Tokens

`.bst` tokens are whitespace-separated. The lexer recognizes:

- **Identifiers**: letters, digits, and the characters
  `. $ -_ /`. Begin with a letter. Identifiers are case-sensitive.
  (Identifiers may not begin with a digit.)
- **Integers**: a `#` immediately followed by an optional sign and
  digits, e.g. `#0`, `#-1`, `#42`. (The `#` prefix distinguishes
  integer literals from identifiers.)
- **String literals**: `" ... "`. No escape sequences.
- **Function literals**: `{ ... }` — a sequence of tokens to be
  executed when the function is called.
- **Quoted function names**: `' NAME` — pushes the name `NAME`
  onto the stack as a function reference (used for passing
  functions as arguments to `while$` / `sort$`).
- **Comments**: `%` to end of line.

### 3.2 Top-level commands

A `.bst` program is a sequence of top-level commands:

| Command | Effect |
|---|---|
| `ENTRY { field-list } { integer-list } { string-list }` | Declares which `.bib` fields the program will read, and per-entry scratch integer/string variables. |
| `STRINGS { name ... }` | Declares global string variables. |
| `INTEGERS { name ... }` | Declares global integer variables. |
| `FUNCTION { NAME } { body }` | Defines a user function. |
| `MACRO { NAME } { "value" }` | Defines a string macro. |
| `READ` | Reads all cited entries from the `.bib` file. Must appear exactly once, after `ENTRY` / `STRINGS` / `INTEGERS` / user `FUNCTION`s are declared. |
| `EXECUTE { NAME }` | Runs NAME once (no current entry). |
| `ITERATE { NAME }` | Runs NAME once per entry in the current entry list, in cite order (after any SORT). |
| `REVERSE { NAME }` | Runs NAME once per entry in reverse order. |
| `SORT` | Sorts the entry list by each entry's `sort.key$` string. |

### 3.3 Stack types

Values on the stack are one of four types:

- **Integer** — 32-bit signed.
- **String** — sequence of bytes.
- **Function** — a reference to a user function or built-in.
- **Missing** — a sentinel representing an absent field value.

Popping a value of the wrong type is an error (the built-in emits
a warning and pushes a default value of the expected type —
`#0` for integer, `""` for string, missing for missing).

### 3.4 Entry scope and fields

Inside `ITERATE` or `REVERSE`, there is a **current entry**. Built-ins
like `cite$` and `type$` access the current entry. Fields declared
in `ENTRY { field-list }` may be accessed by name (e.g. `author`,
`title`) which pushes the field's value onto the stack. If the
field is absent, missing is pushed.

`ENTRY { ... } { integer-list } { string-list }` also declares
per-entry scratch variables. These are separate storage for each
entry, readable and writable via the name.

Special built-in per-entry fields:

- `sort.key$` — the string used by `SORT`.

### 3.5 Built-in functions

The 37 built-in functions:

#### Arithmetic / comparison

| Name | Stack effect | Description |
|---|---|---|
| `>` | `(int int → int)` | Push 1 if second > top, else 0. |
| `<` | `(int int → int)` | Push 1 if second < top, else 0. |
| `=` | `(any any → int)` | Push 1 if equal (same type and value), else 0. Comparing different types is an error; push 0. |
| `+` | `(int int → int)` | Addition. |
| `-` | `(int int → int)` | Subtraction (second minus top). |
| `*` | `(str str → str)` | String concatenation. |
| `:=` | `(value name → )` | Assign value to the global or entry variable named. |

#### String manipulation

| Name | Stack effect | Description |
|---|---|---|
| `add.period$` | `(str → str)` | Appends `.` to the string unless it already ends with `.`, `?`, or `!`. Ignores trailing `}`'s when checking. |
| `change.case$` | `(str str → str)` | Reformat case. Top string is the format: `"t"` (title case — first letter uppercase, rest lowercase, except in brace groups), `"l"` (all lowercase), `"u"` (all uppercase). Case-changing respects brace protection and LaTeX control sequences. |
| `chr.to.int$` | `(str → int)` | Push ASCII code of the single-character string. Error if string length ≠ 1. |
| `int.to.chr$` | `(int → str)` | Push a 1-character string with the given ASCII code. |
| `int.to.str$` | `(int → str)` | Push the decimal representation of the integer. |
| `substring$` | `(str int int → str)` | Pop length, start. Extract substring of `length` chars starting at `start` (1-based). Negative start counts from end. Out-of-range returns an empty string. |
| `text.length$` | `(str → int)` | Push the "text length" — number of characters, treating brace groups and `\foo{...}` specials as length-1, excluding enclosing braces. |
| `text.prefix$` | `(str int → str)` | Return the first `n` text-characters (same counting as `text.length$`). |
| `width$` | `(str → int)` | Push an approximate typeset width in "points-times-100" using a built-in character-width table; used for sort keys. Ignores `\foo` specials, counts brace contents. |
| `purify$` | `(str → str)` | Strip non-alphanumeric characters, replacing spaces with single spaces. Brace contents are kept (purified recursively). Used for generating labels. |

#### Name formatting

| Name | Stack effect | Description |
|---|---|---|
| `format.name$` | `(str int str → str)` | Pop format string, integer N, name-list. Return the Nth name (1-based) formatted per the format string. Format chars: `f` First, `v` von, `l` Last, `j` Jr, with `.` for initials-dot and `~` for ties. Brace-protected portions of the format are preserved literally. |
| `num.names$` | `(str → int)` | Count the `and`-separated names in the string. |

#### Control flow

| Name | Stack effect | Description |
|---|---|---|
| `if$` | `(fn fn int → )` | Pop integer condition, false-branch, true-branch. Execute true-branch if condition ≠ 0, else false-branch. |
| `while$` | `(fn fn → )` | Pop body, condition. Execute condition; if it leaves 0, stop; else execute body; repeat. |
| `skip$` | `( → )` | No-op. |

#### Stack manipulation

| Name | Stack effect | Description |
|---|---|---|
| `pop$` | `(any → )` | Discard top value. |
| `swap$` | `(any any → any any)` | Swap top two values. |
| `duplicate$` | `(any → any any)` | Duplicate top value. |

#### Entry-scope access

| Name | Stack effect | Description |
|---|---|---|
| `cite$` | `( → str)` | Push the current entry's citation key. |
| `type$` | `( → str)` | Push the current entry's type (lowercased). |
| `call.type$` | `( → )` | Call the user-defined function whose name matches the current entry's type; if no such function, call `default.type`. |
| `empty$` | `(any → int)` | Push 1 if top is missing or an empty/whitespace-only string; else 0. |
| `missing$` | `(any → int)` | Push 1 if top is missing; else 0. |
| `preamble$` | `( → str)` | Push the concatenation of all `@preamble` values. |
| `num.names$` (above) | | |

#### Output

| Name | Stack effect | Description |
|---|---|---|
| `write$` | `(str → )` | Append to the output buffer. |
| `newline$` | `( → )` | Emit a newline in the output. (Output does not automatically line-break.) |

#### Character queries

| Name | Stack effect | Description |
|---|---|---|
| `quote$` | `( → str)` | Push the one-character string `"`. |
| `top$` | `( → )` | Print the stack (for debugging). Silent in v0.2 harness use — a no-op is acceptable. |
| `stack$` | `( → )` | Same as `top$` but pop everything. |
| `warning$` | `(str → )` | Emit a warning message; continue. |

### 3.6 Output buffering and line breaking

Real BibTeX automatically wraps output at ~79 characters by
inserting a newline at a suitable space. For this eval the tool
MUST replicate that behavior: when the accumulated "line so far"
exceeds 79 characters and a whitespace is reachable, break at the
latest whitespace <= 79 columns, output a line terminator (see §5.4
for line-ending convention), and continue on a new line with a
2-space leading indent.

Lines explicitly ended by `newline$` do not get the 2-space indent
on the following content.

### 3.7 Sort behavior

`SORT` reorders the entry list by ascending `sort.key$` using a
stable sort. Comparison is byte-wise (not lexicographic on any
particular collation). Entries without a `sort.key$` set sort before
entries with one (they sort as empty strings).

### 3.8 Errors during execution

A runtime error inside a function (e.g. type error, unknown field)
emits a structured warning (§5.3) and substitutes a default value
so execution continues. Programs that reference undefined functions
or variables fail at load time with exit code 1.

## 4. `.bib` and `.bst` file resolution

The tool takes:

1. A `.bib` database file (the `--bib` flag).
2. A `.bst` style file (the `--style` flag).
3. A cite-key list (the `--cites` flag), one key per line; blank lines
   and lines starting with `#` are ignored.

On invocation:

1. Parse the `.bib` file.
2. Parse the `.bst` file.
3. Reduce `.bib` to the cited subset (matching by case-insensitive
   key, preserving declared case in output). Case-insensitive matching
   is how BibTeX itself resolves citations.
4. Resolve `@string` macros and `crossref` inheritance on the cited
   entries.
5. Execute the `.bst` program. `READ` materializes the entry list.
6. The output buffer accumulates `write$` / `newline$` calls and is
   written to the `--output` file when execution completes.

## 5. Output files

### 5.1 `--output` (`.bbl`)

The primary artifact. Byte-for-byte what BibTeX's `.bst` program
produced via `write$` / `newline$`, wrapped at 79 columns per §3.6.

### 5.2 `--log` (JSON, optional)

When `--log <path>` is provided, the tool also writes a structured
JSON log:

```json
{
  "entries_read": integer,
  "entries_cited_found": integer,
  "entries_cited_missing": ["key", ...],
  "functions_defined": integer,
  "macros_defined": ["name", ...],
  "iterations": integer,
  "sorts": integer,
  "warnings": [ <warning object> ]
}
```

### 5.3 Warning objects

Warnings shape:

```json
{"kind": "string", "message": "string", "key": "string?", "field": "string?"}
```

Warning kinds:

- `unresolved_macro` — a `.bib` macro reference was not defined.
- `unresolved_crossref` — a `crossref` target was not found.
- `crossref_cycle` — an immediate two-entry `crossref` cycle was
  detected.
- `duplicate_key` — two `.bib` entries share a key.
- `bst_type_error` — stack type error at runtime; default value
  substituted.
- `bst_undefined_field` — a `.bst` program accessed a field not in
  the current entry (after crossref).
- `bst_undefined_function` — a `.bst` program called an unknown
  function. This is a *hard* error unless the function reference is
  pushed quoted; for quoted pushes it is a load-time warning.
- `cite_not_found` — a cited key did not appear in the `.bib` database.
  The cite key is still attempted in the `ITERATE` list as missing
  if the style file is forgiving; otherwise the iteration skips it.

### 5.4 Line endings

`.bbl` output uses LF (`\n`) line endings regardless of host OS.

## 6. Error handling

Exit codes:

- `0` on successful execution (warnings do not cause non-zero exit).
- `1` on:
  - Unreadable / unparseable `.bib` file.
  - Unreadable / unparseable `.bst` file.
  - Unknown function reference at load time (before READ).
  - Stack underflow at runtime.
  - Missing required CLI argument.
- `2` on unexpected internal error.

On exit 1, the `--output` file contains a structured error JSON:

```json
{"error": {"source": "bib" | "bst" | "runtime",
           "line": integer,
           "column": integer,
           "message": "string"},
 "warnings": [ ... ]}
```

The `--output` file is NOT the `.bbl` in this case; it holds the
error object.

## 7. Character encoding

All input and output is UTF-8. LaTeX control sequences like `{\"o}`
and `\'e` are preserved literally in outputs. `purify$`,
`change.case$`, and `text.length$` respect the brace-protection and
`\...` conventions defined in §3.5.

## 8. Approximations and bounded divergences from BibTeX 0.99c

The historic BibTeX 0.99c binary implements a few operators whose
exact behavior is documented only by the WEB source. Where the
source behavior is either tedious to reproduce or unilluminating for
the stack-interpreter skill this eval measures, this specification
deliberately approximates. Implementations SHOULD follow the
approximation rules given here; tests will only assert on behavior
stated in this section or in §3.5, not on undocumented BibTeX source
behavior outside these bounds.

### 8.1 `width$`

`width$` in BibTeX 0.99c uses the cmr10 character-width table,
producing values in "points × 100" units. Reproducing cmr10
byte-for-byte is out of scope. The specification defines `width$`
functionally as a **deterministic monotone string-width score** with
the following contract:

- Alphanumeric characters contribute **500** units each.
- The space character contributes **250**.
- Any other printable character contributes **300**.
- Brace groups that begin with `\` (e.g. `{\"o}`) contribute the
  width of their interior minus the control sequence — i.e., the
  command prefix is skipped.
- Brace groups that do not begin with `\` contribute the width of
  their interior recursively.

Two strings with the same printable characters (modulo brace
protection) MUST compare equal under `width$`; `width$` comparisons
used for sort keys are meaningful to two-decimal-point ordering.

### 8.2 `change.case$` and LaTeX accent handling

`change.case$` respects brace-protection: characters inside balanced
`{...}` groups are not case-changed. The historic BibTeX descends
into the content of `{\foo{Bar}}` and case-changes only the inner
`{Bar}` contents, not the `\foo` control sequence. This
specification does **not** require that depth of recursion.
Implementations MAY preserve entire brace groups verbatim regardless
of whether they begin with `\`. Tests will not assert on the deep
LaTeX-accent case.

### 8.3 `purify$`

`purify$` strips non-alphanumeric characters and collapses spaces.
Inside a brace group that begins with `\` (a LaTeX control
sequence), the leading `\<command-name>` is dropped and the
interior is `purify$`-ed recursively. Inside a plain brace group,
the interior is `purify$`-ed recursively as if unbraced. These
simplifications match the common-case BibTeX output on textual
input and omit control-sequence-argument edge cases.

### 8.4 `text.length$`

`text.length$` treats each brace group beginning with `\` (a control
sequence) as contributing **1** to the length, regardless of its
interior. Plain brace groups contribute their interior length
recursively. The outer braces themselves contribute 0.

### 8.5 `.bbl` output: semantic vs. byte-exact

The tool's `.bbl` output MUST match the spec's semantics — correct
line wrapping at 79 columns (§3.6), correct output from `write$` /
`newline$`, correct sort order, correct name formatting per
`format.name$`. It is **not** required to be byte-for-byte
compatible with the historic BibTeX 0.99c binary on the above
approximation points. Tests will avoid constructing inputs whose
expected output depends on the specific cmr10 width table or on
deeply nested LaTeX-accent case-changing.
