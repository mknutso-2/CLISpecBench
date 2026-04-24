from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, cast

from clispecbench.pytest_plugin import (
    EvalConfig,
    build_timeout_seconds,
    eval_language,
    language_target,
    prepared_submission,
    pytest_addoption,
    repo_root,
    submission_command,
)

__all__ = [
    "EvalConfig",
    "build_timeout_seconds",
    "eval_language",
    "language_target",
    "prepared_submission",
    "pytest_addoption",
    "repo_root",
    "submission_command",
]

EVAL_CONFIG = EvalConfig(
    task_name="bibtex",
    reference_impl_subdirs={
        "cpp": "Evals/BibTeX/reference-implementation-cpp",
    },
    env_var="SWEBUILDBENCH_BIBTEX_ROOT",
    preferred_executable_name="bibtex",
)


# ---------------------------------------------------------------------------
# Per-domain probe .bst styles. Each probe focuses on one dimension so a bug
# in one dimension doesn't cascade into tests for another.
#
# The v0.2.1 review flagged the original single-probe design as a test-
# independence violation (eval-authoring golden rule 3). v0.3 splits probes
# into narrow single-purpose styles and adds direct-output tests that bypass
# the probe layer entirely.
# ---------------------------------------------------------------------------

# Field probe: emits key=value lines per entry, one field per line. Depends
# only on `write$`, `newline$`, `cite$`, `type$`, `empty$`, `if$`, `*`, and
# field-name lookups.
PROBE_STYLE_FIELDS = r"""
ENTRY { address author booktitle chapter edition editor howpublished
        institution journal key month note number organization pages
        publisher school series title type volume year crossref }
  { }
  { }

FUNCTION {dump.entry}
{ "key=" cite$ * write$
  newline$
  "type=" type$ * write$
  newline$
  author empty$ 'skip$
    { "author=" author * write$ newline$ }
  if$
  title empty$ 'skip$
    { "title=" title * write$ newline$ }
  if$
  journal empty$ 'skip$
    { "journal=" journal * write$ newline$ }
  if$
  year empty$ 'skip$
    { "year=" year * write$ newline$ }
  if$
  publisher empty$ 'skip$
    { "publisher=" publisher * write$ newline$ }
  if$
  month empty$ 'skip$
    { "month=" month * write$ newline$ }
  if$
  editor empty$ 'skip$
    { "editor=" editor * write$ newline$ }
  if$
  "---" write$ newline$
}

READ

ITERATE {dump.entry}
"""


# Name probe: exercises format.name$ by dumping one name per line with its
# four parts. Depends on `format.name$`, `num.names$`, `while$`, `<`, `>`,
# `+`, `-`, `:=`, integer literals, `write$`, `newline$`. Does NOT use
# `empty$` or conditional field output (those are in the field probe), so a
# bug in `empty$` doesn't break name tests.
#
# The probe deliberately uses one-value-per-write$ (no `*` concatenation
# in the output path). An earlier form used `"first=" … format.name$ *
# write$ " " * write$` which underflowed the stack on the trailing
# `" " *` — BibTeX 0.99c tolerates underflow with a substitution warning
# (bibtex.web §7276 `pop_lit_stk`), but CLISpecBench's exit-1 contract
# aborts the whole probe and masks every name-parsing test downstream.
# Writing each literal separately keeps the stack invariant (each
# `write$` pops exactly one string it just pushed) so the probe runs
# under every conforming implementation.
PROBE_STYLE_NAMES = r"""
ENTRY { author }
  { }
  { }

INTEGERS { name.index name.total }

FUNCTION {dump.one.name}
{ "first=" write$
  author name.index "{ff}" format.name$ write$
  " von=" write$
  author name.index "{vv}" format.name$ write$
  " last=" write$
  author name.index "{ll}" format.name$ write$
  " jr=" write$
  author name.index "{jj}" format.name$ write$
  newline$
}

FUNCTION {dump.names}
{ "key=" write$
  cite$ write$
  newline$
  author num.names$ 'name.total :=
  #1 'name.index :=
  { name.index name.total > #0 = }
    { dump.one.name
      name.index #1 + 'name.index := }
  while$
  "---" write$ newline$
}

READ

ITERATE {dump.names}
"""


# Preamble probe: only exercises preamble$, cite$, title-field lookup.
PROBE_STYLE_PREAMBLE = r"""
ENTRY { title }
  { }
  { }

FUNCTION {dump}
{ "preamble=" preamble$ * write$ newline$
  "key=" cite$ * write$ newline$
  "title=" title * write$ newline$
  "---" write$ newline$
}

READ

ITERATE {dump}
"""


# Minimal keys-only probe: cite$ + write$ + newline$ only. Used when we
# want to exercise READ/ITERATE/SORT/REVERSE without depending on any
# field access or conditional logic.
PROBE_STYLE_KEYS = r"""
ENTRY { } { } { }
FUNCTION {dump} { cite$ write$ newline$ }
READ
ITERATE {dump}
"""


def run_bibtex(
    command: tuple[str, ...],
    bib_text: str,
    style_text: str,
    cites: list[str] | str,
    tmp_path: Path,
    *,
    timeout: int = 30,
    expect_exit: int = 0,
    with_log: bool = False,
    aux_text: str | None = None,
) -> tuple[str, dict[str, Any] | None]:
    """Run bibtex with a bib, a style, and cites (or aux). Returns (bbl_text,
    log_dict_or_None). Asserts exit code."""
    bib_file = tmp_path / "refs.bib"
    bst_file = tmp_path / "style.bst"
    output_file = tmp_path / "out.bbl"
    log_file = tmp_path / "out.log" if with_log else None
    bib_file.write_text(bib_text, encoding="utf-8")
    bst_file.write_text(style_text, encoding="utf-8")

    args: list[str] = [
        *command,
        "--bib",
        str(bib_file),
        "--style",
        str(bst_file),
        "--output",
        str(output_file),
    ]
    if aux_text is not None:
        aux_file = tmp_path / "paper.aux"
        aux_file.write_text(aux_text, encoding="utf-8")
        args += ["--aux", str(aux_file)]
    if cites or aux_text is None:
        cites_file = tmp_path / "cites.txt"
        cites_text = cites if isinstance(cites, str) else "\n".join(cites) + "\n"
        cites_file.write_text(cites_text, encoding="utf-8")
        args += ["--cites", str(cites_file)]
    if log_file is not None:
        args += ["--log", str(log_file)]

    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    assert result.returncode == expect_exit, (
        f"bibtex exited with {result.returncode} (expected {expect_exit})\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert output_file.exists(), "output file was not created"
    bbl = output_file.read_text(encoding="utf-8")
    log_dict = None
    if log_file is not None and log_file.exists():
        log_dict = cast(dict[str, Any], json.loads(log_file.read_text(encoding="utf-8")))
    return bbl, log_dict


def run_error(
    command: tuple[str, ...],
    bib_text: str,
    style_text: str,
    cites: list[str] | str,
    tmp_path: Path,
    *,
    timeout: int = 30,
) -> dict[str, Any]:
    bbl, _ = run_bibtex(
        command,
        bib_text,
        style_text,
        cites,
        tmp_path,
        timeout=timeout,
        expect_exit=1,
    )
    return cast(dict[str, Any], json.loads(bbl))


# ---------------------------------------------------------------------------
# Probe-dump parsers (per-probe; deliberately NOT shared between probes).
# ---------------------------------------------------------------------------


def parse_field_dump(bbl: str) -> list[dict[str, str]]:
    """Parse output of PROBE_STYLE_FIELDS / PROBE_STYLE_PREAMBLE into records."""
    records: list[dict[str, str]] = []
    cur: dict[str, str] = {}
    for line in bbl.split("\n"):
        if line == "---":
            if cur:
                records.append(cur)
                cur = {}
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            cur[k] = v
    if cur:
        records.append(cur)
    return records


# Back-compat alias for existing tests that imported parse_dump.
parse_dump = parse_field_dump


def parse_name_dump(bbl: str) -> list[dict[str, Any]]:
    """Parse output of PROBE_STYLE_NAMES."""
    entries: list[dict[str, Any]] = []
    cur_key: str | None = None
    cur_names: list[dict[str, str]] = []
    for raw in bbl.split("\n"):
        line = raw
        if line == "---":
            if cur_key is not None:
                entries.append({"key": cur_key, "names": cur_names})
            cur_key = None
            cur_names = []
            continue
        if line.startswith("key="):
            cur_key = line[len("key=") :]
            continue
        if line.startswith("first="):
            parts: dict[str, str] = {}
            buf = line
            for label in ("first=", "von=", "last=", "jr="):
                if label in buf:
                    idx = buf.index(label)
                    buf = buf[idx:]
                    next_idx = len(buf)
                    for other in ("first=", "von=", "last=", "jr="):
                        if other == label:
                            continue
                        if other in buf[len(label) :]:
                            o_idx = buf.index(other, len(label))
                            if o_idx < next_idx:
                                next_idx = o_idx
                    val = buf[len(label) : next_idx].rstrip()
                    parts[label[:-1]] = val
                    buf = buf[next_idx:]
            cur_names.append(parts)
    return entries
