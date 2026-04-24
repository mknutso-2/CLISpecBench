The tool must accept these command-line flags:

- `--bib <path>`: path to the `.bib` database file.
- `--style <path>`: path to the `.bst` style file.
- `--cites <path>`: path to a plain-text file of citation keys, one per
  line. Blank lines and lines starting with `#` are ignored.
- `--aux <path>`: alternative to `--cites`. Path to a LaTeX `.aux`
  file; the tool extracts citation keys from `\citation{key1,key2,...}`
  commands (one or more keys per command, comma-separated, whitespace
  permitted; multiple `\citation{}` commands accumulate). When both
  `--cites` and `--aux` are given, the cite-key lists are concatenated
  in order (cites first, aux second) before deduplication. At least
  one of `--cites` / `--aux` is required.
- `--output <path>`: path where the `.bbl` is written on success (or
  the error JSON is written on failure).
- `--log <path>`: optional — path to write a structured JSON log.

On **successful execution** (exit 0) the `--output` file is the
`.bbl` produced by executing the `.bst` program's `write$` and
`newline$` calls. Line endings are LF (`\n`). Output is UTF-8. Lines
wrap at 79 columns per the specification in `docs/`.

On **parse/exec failure** (exit 1) the `--output` file contains an
error JSON:

```json
{
  "error": {
    "source": "bib" | "bst" | "runtime",
    "line": integer,
    "column": integer,
    "message": "string"
  },
  "warnings": [ <warning object> ]
}
```

The optional `--log` file, if requested, is always a JSON object:

```json
{
  "entries_read": integer,
  "entries_cited_found": integer,
  "entries_cited_missing": ["key", ...],
  "functions_defined": integer,
  "macros_defined": ["name", ...],
  "iterations": integer,
  "sorts": integer,
  "reverse_iterations": integer,
  "execute_calls": integer,
  "warnings": [ <warning object> ]
}
```

Where each warning is:

```json
{"kind": "string", "message": "string", "key": "string?",
  "field": "string?", "line": "integer?", "column": "integer?"}
```

Top-level JSON key order is not asserted — tests use `.get()`.
Warning arrays preserve the chronological order in which warnings
were generated.

Warning `kind` values emitted by this tool. The tool emits one of
these canonical kind strings for every warning; tests assert on
these exact strings, so a submission that uses a synonym (e.g.
`"crossref_missing"` instead of `"unresolved_crossref"`) will fail
the warning-kind checks.

- `unresolved_crossref` — `crossref` points at a non-existent key.
- `crossref_cycle` — `crossref` chain contains a cycle.
- `unresolved_macro` — reference to an unresolved `@string` macro.
- `duplicate_key` — two `.bib` entries share a citation key.
- `bst_type_error` — stack type error at runtime on a built-in;
  the built-in recovers by pushing a default value rather than
  aborting the run (so tests see the warning and still get a
  well-formed `.bbl`).
- `bst_undefined_field` — a `.bst` program accessed a field not
  declared in the entry type or absent from the current entry.
- `bst_undefined_function` — a `.bst` program called or assigned
  to an identifier that was never declared.

## Exit codes

- `0`: successful execution. Warnings are fine.
- `1`: malformed `.bib` or `.bst`, unreadable input, runtime stack
  underflow, unknown function reference at load time, missing
  required flag.
- `2`: unexpected internal error.
