"""RFC 6868 parameter-value escaping.

RFC 6868 §3 defines a `^`-based escape mechanism for iCalendar parameter
values so that characters otherwise forbidden by RFC 5545 §3.1 syntax (line
breaks, double-quotes, and the escape character itself) can be embedded in a
parameter value:

    ^n  →  U+000A LINE FEED (or an appropriate formatted line break)
    ^'  →  U+0022 QUOTATION MARK
    ^^  →  U+005E CIRCUMFLEX ACCENT

Any `^` followed by a character other than those three MUST be left intact
(both the `^` and the following character), i.e. `^x` decodes to the literal
two-character string `^x` (RFC 6868 §3, last bullet of the "parsing" list).

The escaping applies to parameter values only; it MUST NOT be applied to
property values (those continue to use the RFC 5545 `\\`-escaping mechanism).

Where a parse-level error is worth surfacing, this tool uses the warning kind
`param_escape_invalid` (listed in technical-requirements-prompt.md).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import find_event, run_parse, wrap_event


def _attendees_of(ev: dict[str, Any]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], ev.get("attendees") or [])

# ---------------------------------------------------------------------------
# ^' (encoded double-quote) inside unquoted param value
# ---------------------------------------------------------------------------


def test_param_escape_caret_apostrophe_decodes_to_quote(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 6868 §3.1 example: the encoded parameter value `George Herman ^'Babe^'
    Ruth` decodes to `George Herman "Babe" Ruth`. Both `^'` sequences become a
    single U+0022 QUOTATION MARK character."""
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "ATTENDEE;CN=George Herman ^'Babe^' Ruth:mailto:babe@example.com\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(out, "e1")
    attendees = _attendees_of(ev)
    assert len(attendees) == 1
    assert attendees[0].get("cn") == 'George Herman "Babe" Ruth'


# ---------------------------------------------------------------------------
# ^n (encoded line break) inside quoted param value
# ---------------------------------------------------------------------------


def test_param_escape_caret_n_decodes_to_newline(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 6868 §3 defines `^n` as the encoded form of a formatted line break.
    A value with `Line1^nLine2` decodes to `Line1\\nLine2` (real LF between
    segments)."""
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        'ATTENDEE;CN="Line1^nLine2":mailto:x@example.com\n'
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(out, "e1")
    attendees = _attendees_of(ev)
    assert len(attendees) == 1
    assert attendees[0].get("cn") == "Line1\nLine2"


# ---------------------------------------------------------------------------
# ^^ (encoded caret)
# ---------------------------------------------------------------------------


def test_param_escape_double_caret_decodes_to_single_caret(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 6868 §3: `^^` decodes to a single `^` character. This is required so
    that a literal `^` can be represented unambiguously in a parameter value."""
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "ATTENDEE;CN=a^^b:mailto:x@example.com\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(out, "e1")
    attendees = _attendees_of(ev)
    assert len(attendees) == 1
    assert attendees[0].get("cn") == "a^b"


def test_param_escape_three_carets(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """`^^^'` = `^^` + `^'` = literal `^` + literal `"`. This checks that the
    decoder greedily consumes from left to right per RFC 6868 §3."""
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "ATTENDEE;CN=a^^^'b:mailto:x@example.com\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(out, "e1")
    attendees = _attendees_of(ev)
    assert len(attendees) == 1
    assert attendees[0].get("cn") == 'a^"b'


# ---------------------------------------------------------------------------
# Unknown ^X sequence: both the caret and the next character are kept literally
# ---------------------------------------------------------------------------


def test_param_escape_unknown_sequence_preserves_both_chars(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 6868 §3: "if a ^ is followed by any character other than [n, ', ^],
    parsers MUST leave both the ^ and the following character in place".
    So `^x` in a parameter value decodes to the literal two-character string
    `^x`."""
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "ATTENDEE;CN=foo^xbar:mailto:x@example.com\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(out, "e1")
    attendees = _attendees_of(ev)
    assert len(attendees) == 1
    assert attendees[0].get("cn") == "foo^xbar"


def test_param_escape_trailing_caret_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A trailing `^` (with no following character) is an invalid sequence. Per
    the "leave both in place" rule, the `^` is preserved literally. Some
    implementations may also emit a `param_escape_invalid` warning; either
    outcome is acceptable — we only assert the literal-preservation half."""
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "ATTENDEE;CN=trailing^:mailto:x@example.com\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(out, "e1")
    attendees = _attendees_of(ev)
    assert len(attendees) == 1
    assert attendees[0].get("cn") == "trailing^"


# ---------------------------------------------------------------------------
# Escape applies only to param values, NOT to property values
# ---------------------------------------------------------------------------


def test_param_escape_not_applied_to_property_text_value(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 6868 §3 restricts the `^`-escape mechanism to parameter values only.
    A property text value containing `^n` must remain the literal two-character
    string `^n` (the RFC 5545 property-value text-escape mechanism uses
    backslashes, not carets, for line breaks)."""
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "SUMMARY:literal ^n in property value\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(out, "e1")
    assert ev.get("summary") == "literal ^n in property value"


# ---------------------------------------------------------------------------
# Escape inside a *quoted* parameter value — must still be decoded
# ---------------------------------------------------------------------------


def test_param_escape_works_inside_quoted_value(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 6868 §3: "the ^-escaping mechanism can be used when the value is
    either unquoted or quoted". So a DQUOTE-wrapped parameter value containing
    `^n` must still decode the `^n` sequence to a line feed."""
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        'ATTENDEE;CN="a^nb":mailto:x@example.com\n'
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(out, "e1")
    attendees = _attendees_of(ev)
    assert len(attendees) == 1
    assert attendees[0].get("cn") == "a\nb"


# ---------------------------------------------------------------------------
# Raw properties must expose the *decoded* value, not the raw escaped bytes
# ---------------------------------------------------------------------------


def test_param_escape_reflected_in_raw_properties(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """`raw_properties[n].params` MUST store the DECODED parameter value per
    RFC 6868's "parsing" step — a downstream consumer should not have to
    re-decode. This mirrors how `params.TZID` already appears un-escaped in
    `raw_properties` for existing tests."""
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "ATTENDEE;CN=George ^'Babe^' Ruth:mailto:babe@example.com\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(out, "e1")
    raw = cast(list[dict[str, Any]], ev.get("raw_properties") or [])
    found_decoded = False
    for p in raw:
        if p.get("name") == "ATTENDEE":
            params = cast(dict[str, Any], p.get("params") or {})
            cn = params.get("CN")
            if cn == 'George "Babe" Ruth':
                found_decoded = True
                break
    assert found_decoded, (
        "ATTENDEE's CN param in raw_properties should be RFC 6868-decoded, "
        "not the raw escaped bytes"
    )


# ---------------------------------------------------------------------------
# Combined escapes + interaction with LANGUAGE / other params on same property
# ---------------------------------------------------------------------------


def test_param_escape_multiple_params_with_escapes(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A property with multiple parameters, each independently needing decoding,
    must not have cross-contamination. CN=`a"b`, ROLE=REQ-PARTICIPANT,
    PARTSTAT=ACCEPTED must all parse correctly."""
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "ATTENDEE;CN=a^'b;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED:mailto:x@example.com\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(out, "e1")
    attendees = _attendees_of(ev)
    assert len(attendees) == 1
    att = attendees[0]
    assert att.get("cn") == 'a"b'
    assert att.get("role") == "REQ-PARTICIPANT"
    assert att.get("partstat") == "ACCEPTED"
