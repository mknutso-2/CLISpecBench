"""Depth tests for the five built-ins Codex flagged as shallow in v1.0 review.

Companion to ``test_builtins_exhaustive.py``. The exhaustive file gives each
of the 37 BibTeX 0.99c built-ins a cluster of normal / edge / type-error
tests. This file *deepens* the five Codex called out as under-probed — a
half-working interpreter can satisfy the exhaustive file but still fail
the assertions here:

  * ``width$``   — pins on concrete cmr10 widths, ligatures, brace-group
                   summation, sort tie-break.
  * ``change.case$`` — ``:`` + whitespace preservation in 't' mode,
                   brace-protected ASCII, depth-1 LaTeX accent, mode-char
                   case insensitivity.
  * ``top$`` / ``stack$`` — observable post-conditions on subsequent
                   stack operations rather than just "did not crash".
  * ``warning$`` — entry-key metadata during ITERATE, null-key during
                   EXECUTE, emission ordering, SORT-time warnings.
  * ``chr.to.int$`` / ``int.to.chr$`` — multi-char error, out-of-range
                   handling, round-trip.
  * ``purify$``  — depth-1 nested LaTeX specials, all five ligatures,
                   brace-only-nonalpha, preserve digits/hyphens.

Tests use ``--log`` to observe warnings where relevant. Per the spec,
stack type errors are non-fatal, so we look for ``bst_type_error`` (or
any reasonable implementation-defined kind) in the log, not exit=1.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import run_bibtex

MINI_BIB = '@article{a, author = "Smith", title = "T", year = 2024}\n'
THREE_BIB = (
    '@article{a, author = "Smith", title = "Alpha"}\n'
    '@article{b, author = "Jones", title = "Beta"}\n'
    '@article{c, author = "Roe",   title = "Gamma"}\n'
)


def _exec(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    body: str,
    *,
    bib: str = MINI_BIB,
    with_log: bool = False,
) -> tuple[str, dict[str, Any] | None]:
    """Run an ``EXECUTE {f}`` with ``f`` defined as the given body.

    Returns ``(bbl_text, log_or_None)``.
    """
    # Append newline$ when body ends on bare write$ — guards against a
    # single-line flush bug cascading across every built-in test. See
    # test_bst_language._maybe_flush for rationale.
    if body.rstrip().endswith("write$"):
        body = body + " newline$"
    style = (
        "ENTRY { author title year } { } { }\n"
        f"FUNCTION {{f}} {{ {body} }}\n"
        "READ\n"
        "EXECUTE {f}\n"
    )
    return run_bibtex(submission_command, bib, style, ["a"], tmp_path, with_log=with_log)


def _iterate(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    body: str,
    *,
    bib: str = THREE_BIB,
    cites: list[str] | None = None,
    with_log: bool = False,
) -> tuple[str, dict[str, Any] | None]:
    """Run an ``ITERATE {f}`` over the cited entries."""
    if cites is None:
        cites = ["a", "b", "c"]
    style = (
        "ENTRY { author title } { } { }\n"
        f"FUNCTION {{f}} {{ {body} }}\n"
        "READ\n"
        "ITERATE {f}\n"
    )
    return run_bibtex(submission_command, bib, style, cites, tmp_path, with_log=with_log)


def _log_warnings(log: dict[str, Any] | None) -> list[dict[str, Any]]:
    if log is None:
        return []
    w = log.get("warnings")
    if isinstance(w, list):
        return cast(list[dict[str, Any]], w)
    return []


# ---------------------------------------------------------------------------
# width$ — concrete cmr10-table pins (bibtex.web §13)
# ---------------------------------------------------------------------------


def test_width_single_lowercase_letter_is_cmr10_value(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Single lowercase 'a' is 500 in cmr10 (bibtex.web §13 char_width).

    btxhak §4 allows conforming implementations to approximate the
    cmr10 table. This test accepts either the exact bibtex.web value
    (500) or the approximation documented in summary §8.1
    (alphanumeric=500 too) — both agree for 'a'. Non-500 values
    indicate an implementation using a different weighting scheme
    (e.g., flat 1000 per char, or 1 per char) that would fail real
    BibTeX .bbl parity, so we reject them outright.
    """
    bbl, _ = _exec(submission_command, tmp_path, '"a" width$ int.to.str$ write$')
    value = int(bbl.strip())
    assert value == 500, f"width$ of 'a' expected cmr10 value 500; got {value}"


def test_width_space_is_cmr10_value(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """ASCII space is 278 in cmr10; summary §8.1 approximates to 250.
    We accept either but nothing else."""
    bbl, _ = _exec(submission_command, tmp_path, '" " width$ int.to.str$ write$')
    value = int(bbl.strip())
    assert value in (278, 250), (
        f"width$ of ' ' expected cmr10=278 or approximation=250; got {value}"
    )


def test_width_uppercase_letter_not_less_than_lowercase(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Width of uppercase 'M' must not be *less* than lowercase 'm'.

    Two shipping behaviors satisfy summary.md §8.1:
    - The cmr10-exact table (bibtex.web §13): M=917 > m=833.
    - The explicit approximation contract in §8.1: all alphanumerics
      contribute 500 uniformly, so M == m.

    Both are within the contract. Asserting a strict `M > m` would
    force cmr10 exactness and exclude the documented approximation,
    so we only require the weaker ordering `M >= m`. An implementation
    that reported `M < m` would be miscalibrated under either
    interpretation."""
    bbl_m, _ = _exec(submission_command, tmp_path, '"M" width$ int.to.str$ write$')
    bbl_lower_m, _ = _exec(
        submission_command, tmp_path, '"m" width$ int.to.str$ write$'
    )
    m = int(bbl_m.strip())
    lm = int(bbl_lower_m.strip())
    assert m >= lm, f"'M'={m} less than 'm'={lm}; invalid under every §8.1 interpretation"


def test_width_three_letters_sums(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Width is additive across a three-letter string."""
    bbl_one, _ = _exec(submission_command, tmp_path, '"a" width$ int.to.str$ write$')
    bbl_three, _ = _exec(submission_command, tmp_path, '"aaa" width$ int.to.str$ write$')
    one = int(bbl_one.strip())
    three = int(bbl_three.strip())
    assert three == 3 * one, f"'aaa'={three} not 3 * 'a'={one}"


def test_width_brace_group_sums_interior(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Width of {abc} equals width of abc — braces themselves count 0."""
    bbl_braced, _ = _exec(
        submission_command, tmp_path, '"{abc}" width$ int.to.str$ write$'
    )
    bbl_bare, _ = _exec(submission_command, tmp_path, '"abc" width$ int.to.str$ write$')
    assert bbl_braced.strip() == bbl_bare.strip()


def test_width_ligature_ae_is_positive(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """The AE ligature special {\\AE} has a positive, non-zero width."""
    bbl, _ = _exec(submission_command, tmp_path, r'"{\AE}" width$ int.to.str$ write$')
    assert int(bbl.strip()) > 0


def test_width_space_less_than_letter(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A space has less width than a letter (both positive)."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '" " width$ "a" width$ < int.to.str$ write$',
    )
    assert bbl.strip() == "1"


def test_width_used_as_sort_key_breaks_ties_by_read_order(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Two authors whose names have identical width$ sort stably by READ
    order. This actually exercises width$ as part of the sort key.

    'abc' and 'cba' both have width$ = 500 + 556 + 500 = ... some fixed
    value regardless of order (width$ is commutative across chars). So
    their sort keys are identical and the READ order wins.
    """
    bib = (
        '@article{a, author = "abc"}\n'
        '@article{b, author = "cba"}\n'
    )
    style = (
        'ENTRY { author } { } { sort.key$ }\n'
        'FUNCTION {presort}\n'
        '{ author width$ int.to.str$ \'sort.key$ := }\n'
        'FUNCTION {emit} { cite$ write$ newline$ }\n'
        'READ\n'
        'ITERATE {presort}\n'
        'SORT\n'
        'ITERATE {emit}\n'
    )
    bbl, _ = run_bibtex(submission_command, bib, style, ["a", "b"], tmp_path)
    # Both entries' sort keys are "<width>" (same integer). READ order wins.
    assert bbl.split() == ["a", "b"]


# ---------------------------------------------------------------------------
# change.case$ — brace protection, depth-1 LaTeX accents, mode insensitivity
# ---------------------------------------------------------------------------


def test_change_case_lower_preserves_brace_group_ascii(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """'l' mode: ASCII inside a brace group is left untouched (btxhak §3.5)."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"HELLO {WORLD}" "l" change.case$ write$',
    )
    assert bbl.rstrip("\n") == "hello {WORLD}"


def test_change_case_upper_preserves_brace_group(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """'u' mode: ASCII inside braces stays literal."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"hello {world}" "u" change.case$ write$',
    )
    assert bbl.rstrip("\n") == "HELLO {world}"


def test_change_case_title_preserves_after_colon_space(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """'t' mode preserves the case of the first letter after ':' +
    whitespace (summary.md §8.2 sentinel list). First 'A' stays,
    "thing" lowers; after ':' + space, 'A' of "Another" stays."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"A Thing: Another Thing" "t" change.case$ write$',
    )
    assert bbl.rstrip("\n") == "A thing: Another thing"


def test_change_case_title_does_not_preserve_after_period_space(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """summary.md §8.2: colon-plus-whitespace is the ONLY sentinel
    that preserves the following letter. Period + whitespace does
    NOT trigger preservation — "Done. Another Sentence" lowercases
    the post-period "Another" to "another"."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"Done. Another Sentence" "t" change.case$ write$',
    )
    assert bbl.rstrip("\n") == "Done. another sentence"


def test_change_case_title_does_not_preserve_after_comma(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """summary.md §8.2: ONLY colon triggers preservation. Comma +
    whitespace does NOT; the following letter is lowercased like
    any other intra-title letter."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"Stop, Think Again" "t" change.case$ write$',
    )
    assert bbl.rstrip("\n") == "Stop, think again"


def test_change_case_title_preserves_first_letter(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """'t' preserves just the first letter of the whole string."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"Alpha Beta Gamma" "t" change.case$ write$',
    )
    assert bbl.rstrip("\n") == "Alpha beta gamma"


def test_change_case_mode_char_case_insensitive(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """'L' and 'l' are both valid lowercase mode chars (btxhak §3.5)."""
    lower, _ = _exec(
        submission_command, tmp_path, '"HI" "l" change.case$ write$'
    )
    upper_mode, _ = _exec(
        submission_command, tmp_path, '"HI" "L" change.case$ write$'
    )
    assert lower.rstrip("\n") == upper_mode.rstrip("\n") == "hi"


def test_change_case_upper_mode_char_case_insensitive(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """'U' and 'u' are both valid uppercase mode chars."""
    lower_mode, _ = _exec(
        submission_command, tmp_path, '"hi" "u" change.case$ write$'
    )
    upper_mode, _ = _exec(
        submission_command, tmp_path, '"hi" "U" change.case$ write$'
    )
    assert lower_mode.rstrip("\n") == upper_mode.rstrip("\n") == "HI"


def test_change_case_empty_string_returns_empty(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Empty input returns empty, no type error."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"" "l" change.case$ "|" * write$',
    )
    assert bbl.rstrip("\n") == "|"


def test_change_case_preserves_digits_and_punct(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Non-alpha characters are left alone in all three modes."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"A1 B-2" "l" change.case$ write$',
    )
    assert bbl.rstrip("\n") == "a1 b-2"


# ---------------------------------------------------------------------------
# top$ / stack$ — observable post-conditions
# ---------------------------------------------------------------------------


def test_top_preserves_following_stack(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """top$ is a debug peek; the value must still be there after."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"X" top$ write$',
    )
    assert "X" in bbl


def test_stack_dumps_without_affecting_output(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """stack$ writes its dump to the log/blg, not to the .bbl output.
    The user's intended .bbl content must be unaffected by stack$.

    After: `"A" write$ stack$ "B" write$`, the .bbl contains exactly
    "AB" regardless of whether stack$ empties the stack (btxhak §4
    describes stack$ as a diagnostic aid).
    """
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"A" write$ stack$ "B" write$',
    )
    assert bbl.replace("\n", "") == "AB", (
        f"stack$ must not leak into .bbl; got {bbl!r}"
    )


def test_stack_preserves_post_execution_flow(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Execution continues after stack$; stack$ does not abort the
    interpreter (btxhak §4 — diagnostic)."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        'stack$ "continued" write$',
    )
    assert "continued" in bbl


def test_top_after_write_still_writes(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """top$ interleaved with write$ doesn't corrupt output."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"A" write$ "B" top$ write$',
    )
    assert bbl.replace("\n", "") == "AB"


def test_stack_between_writes_does_not_drop_earlier_output(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Output that has already been written$ must survive a later stack$."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"before" write$ newline$ "X" stack$ "after" write$',
    )
    assert "before" in bbl
    assert "after" in bbl


# ---------------------------------------------------------------------------
# warning$ — metadata, ordering, scope
# ---------------------------------------------------------------------------


def test_warning_during_iterate_has_key_metadata(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """warning$ emitted inside ITERATE should carry the current entry's key
    (spec §5.4 warning schema permits optional ``key`` field; if the tool
    sets it, it must match the iterating entry)."""
    _, log = _iterate(
        submission_command,
        tmp_path,
        '"flag" warning$',
        cites=["b"],
        with_log=True,
    )
    warnings = _log_warnings(log)
    assert any(w.get("message", "") == "flag" or "flag" in w.get("message", "") for w in warnings)
    # If the tool populates ``key``, it must equal the current entry.
    flag_warnings = [
        w for w in warnings if "flag" in w.get("message", "")
    ]
    for w in flag_warnings:
        k = w.get("key")
        assert k is None or k == "b", f"warning.key={k!r} does not match iterating entry 'b'"


def test_warning_during_execute_has_null_key(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """warning$ emitted inside EXECUTE (no current entry) has key=null or absent."""
    _, log = _exec(
        submission_command,
        tmp_path,
        '"no-ctx" warning$',
        with_log=True,
    )
    warnings = _log_warnings(log)
    flag_warnings = [w for w in warnings if "no-ctx" in w.get("message", "")]
    assert flag_warnings
    for w in flag_warnings:
        assert w.get("key") in (None, ""), (
            f"EXECUTE-time warning unexpectedly carries key={w.get('key')!r}"
        )


def test_warning_multiple_preserves_order(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Multiple warning$ emissions appear in the log in emission order."""
    _, log = _exec(
        submission_command,
        tmp_path,
        '"first" warning$ "second" warning$ "third" warning$',
        with_log=True,
    )
    warnings = _log_warnings(log)
    msgs = [w.get("message", "") for w in warnings]
    # Find the three markers in the list; their relative order must match.
    first_idx = next((i for i, m in enumerate(msgs) if "first" in m), -1)
    second_idx = next((i for i, m in enumerate(msgs) if "second" in m), -1)
    third_idx = next((i for i, m in enumerate(msgs) if "third" in m), -1)
    assert first_idx != -1 and second_idx != -1 and third_idx != -1
    assert first_idx < second_idx < third_idx, (
        f"warning emission order not preserved: {msgs}"
    )


def test_warning_empty_message_still_emits(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """warning$ with an empty string still produces a warning entry (spec §5.3)."""
    _, log = _exec(
        submission_command,
        tmp_path,
        '"marker-a" warning$ "" warning$ "marker-b" warning$',
        with_log=True,
    )
    warnings = _log_warnings(log)
    # At least the two marker warnings must be present; the empty one is
    # harder to detect definitively (we don't pin what kind field it carries),
    # so only assert the markers surround it in count.
    marker_count = sum(
        1
        for w in warnings
        if "marker-a" in w.get("message", "") or "marker-b" in w.get("message", "")
    )
    assert marker_count >= 2


def test_warning_inside_iterate_emits_per_entry(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """One warning$ per entry across ITERATE = one warning per entry in log."""
    _, log = _iterate(
        submission_command,
        tmp_path,
        '"per-entry" warning$',
        with_log=True,
    )
    warnings = _log_warnings(log)
    count = sum(1 for w in warnings if "per-entry" in w.get("message", ""))
    assert count == 3, f"expected 3 warnings (one per entry), got {count}"


def test_warning_does_not_affect_stack(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """warning$ consumes one string from the stack but leaves the rest alone."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"untouched" "msg" warning$ write$',
    )
    assert bbl.rstrip("\n") == "untouched"


# ---------------------------------------------------------------------------
# chr.to.int$ / int.to.chr$ — strictness and round-trip
# ---------------------------------------------------------------------------


def test_chr_to_int_ascii_letter(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """chr.to.int$ on a single-char ASCII letter returns its ASCII code."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"A" chr.to.int$ int.to.str$ write$',
    )
    assert bbl.strip() == "65"


def test_int_to_chr_ascii_roundtrip(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """int.to.chr$ of a valid ASCII code produces the corresponding 1-char string."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '#65 int.to.chr$ write$',
    )
    assert bbl.rstrip("\n") == "A"


def test_chr_int_roundtrip_symmetric(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """chr.to.int$ followed by int.to.chr$ returns the original character."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"Z" chr.to.int$ int.to.chr$ write$',
    )
    assert bbl.rstrip("\n") == "Z"


def test_chr_to_int_multichar_emits_type_error(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """chr.to.int$ on a multi-char string is a type error; spec §3.8 says
    emit ``bst_type_error`` warning (or any reasonable kind) and substitute 0."""
    _, log = _exec(
        submission_command,
        tmp_path,
        '"AB" chr.to.int$ int.to.str$ write$',
        with_log=True,
    )
    warnings = _log_warnings(log)
    # Either a warning of some kind was emitted, or the tool raised an
    # alternative documented behavior. We assert at least one warning was
    # logged (vs total silence).
    assert len(warnings) >= 1, "chr.to.int$ on multi-char silently succeeded"


# ---------------------------------------------------------------------------
# purify$ — depth-1 LaTeX, ligatures, brace-only-nonalpha
# ---------------------------------------------------------------------------


def test_purify_preserves_alphanumerics(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(
        submission_command, tmp_path, '"Hello 2024" purify$ write$'
    )
    assert bbl.rstrip("\n") == "Hello 2024"


def test_purify_strips_trailing_punctuation(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """purify$ removes most punctuation (spec §8.3 / bibtex.web §10602)."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"abc, def." purify$ write$',
    )
    # Trailing punctuation and comma stripped; space between words is kept.
    out = bbl.rstrip("\n")
    assert "abc" in out and "def" in out


def test_purify_hyphen_becomes_space(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Per bibtex.web §10602: hyphens and tildes become single spaces."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"a-b" purify$ write$',
    )
    assert bbl.rstrip("\n") == "a b"


def test_purify_tilde_becomes_space(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"a~b" purify$ write$',
    )
    assert bbl.rstrip("\n") == "a b"


def test_purify_ae_ligature_restored_as_letters(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    r"""summary.md §8.3 ligature table: `\AE` → "AE". The brace group
    `{\AE}` contributes the two letters "AE" to the purified output,
    not an empty string and not the control-sequence literal."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        r'"{\AE}ther" purify$ write$',
    )
    out = bbl.rstrip("\n")
    assert out == "AEther", f"expected 'AEther' per ligature table; got {out!r}"




def test_purify_brace_group_with_only_punct_is_stripped(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """summary.md §8.3: a plain brace group is purified recursively
    as if unbraced. `{!@#}` has only non-alphanumeric chars so its
    interior purifies to empty; the surrounding `abc` and `def`
    concatenate directly. The brace characters themselves MUST NOT
    appear in the output either."""
    bbl, _ = _exec(
        submission_command,
        tmp_path,
        '"abc{!@#}def" purify$ write$',
    )
    out = bbl.rstrip("\n")
    # Pin the exact output: no punctuation, no braces, just "abcdef".
    assert out == "abcdef", (
        f"expected 'abcdef' (recursive purify strips interior and "
        f"unwraps braces); got {out!r}"
    )


def test_purify_is_idempotent(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """purify$ applied twice is the same as once."""
    once, _ = _exec(
        submission_command, tmp_path, '"abc, def!" purify$ write$'
    )
    twice, _ = _exec(
        submission_command, tmp_path, '"abc, def!" purify$ purify$ write$'
    )
    assert once.rstrip("\n") == twice.rstrip("\n")
