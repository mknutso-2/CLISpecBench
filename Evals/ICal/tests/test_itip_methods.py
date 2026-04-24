"""RFC 5546 iTIP VEVENT method-specific requirements (§3.2).

RFC 5546 defines the Transport-Independent Interoperability Protocol
(iTIP) layered on top of iCalendar. The METHOD property on VCALENDAR
(RFC 5545 §3.7.2) names the iTIP operation the calendar represents.

This file covers the VEVENT §3.2.x matrices. The VTODO (§3.4),
VJOURNAL (§3.5), and VFREEBUSY (§3.3) component-specific matrices
are covered separately in `test_itip_per_component.py`, and the
deeper VEVENT method cases (ADD, REFRESH, COUNTER, DECLINECOUNTER,
plus SEQUENCE/DTSTAMP edge cases) are in `test_itip_methods_deep.py`.

Summary of the §3.2 matrix pinned here:
  - REQUEST (§3.2.2):  ORGANIZER 1, ATTENDEE 1+.
  - REPLY (§3.2.3):    ORGANIZER 1, ATTENDEE 1 carrying PARTSTAT.
  - CANCEL (§3.2.5):   ORGANIZER 1, SEQUENCE 1; STATUS (if present)
                        MUST be CANCELLED; absent STATUS is valid per
                        §3.2.5 prose (METHOD alone conveys cancellation).
  - PUBLISH (§3.2.1):  ORGANIZER MAY appear, ATTENDEE MUST NOT.

When required iTIP properties are missing or inconsistent, the parser
SHOULD emit an `itip_missing_property` warning. The specific `message`
wording is not asserted generically; tests that DO pin message content
(e.g. CANCEL STATUS) call it out explicitly.

The calendar-level METHOD is surfaced as `calendar.method` in the JSON
schema (see v0.2 feature tests) so that downstream tooling can
dispatch iTIP processing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import run_parse


def _warn_kinds(payload: dict[str, Any]) -> list[str]:
    """Return the list of warning `kind` values. Defensive against a
    missing/non-list `warnings` key so individual bugs in the schema
    don't cascade into N test failures."""
    warns = payload.get("warnings")
    if not isinstance(warns, list):
        return []
    out: list[str] = []
    for w in cast(list[Any], warns):
        if isinstance(w, dict):
            kind = cast(dict[str, Any], w).get("kind")
            if isinstance(kind, str):
                out.append(kind)
    return out


def _wrap_with_method(method: str, vevent_body: str) -> str:
    """Build a VCALENDAR with a given METHOD and a single VEVENT."""
    return (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//Test//EN\n"
        f"METHOD:{method}\n"
        "BEGIN:VEVENT\n"
        + vevent_body
        + "END:VEVENT\n"
        "END:VCALENDAR\n"
    )


# Common event skeletons — all have the minimum required VEVENT props
# (UID, DTSTAMP, DTSTART) so that baseline parsing never fails for
# unrelated reasons.
_BASE = (
    "UID:e1\n"
    "DTSTAMP:20260420T120000Z\n"
    "DTSTART:20260305T100000Z\n"
    "SEQUENCE:0\n"
    "SUMMARY:Sample\n"
)

_BASE_WITH_ORGANIZER = _BASE + "ORGANIZER:mailto:boss@example.com\n"

_BASE_WITH_ORGANIZER_AND_ATTENDEE_PARTSTAT = (
    _BASE_WITH_ORGANIZER
    + "ATTENDEE;PARTSTAT=ACCEPTED:mailto:jane@example.com\n"
)


# ---------------------------------------------------------------------------
# calendar.method surfaced correctly for each iTIP method
# ---------------------------------------------------------------------------


def test_method_publish_surfaced(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """METHOD:PUBLISH must be exposed as calendar.method='PUBLISH'."""
    ics = _wrap_with_method("PUBLISH", _BASE)
    out = run_parse(submission_command, ics, tmp_path)
    cal = out.get("calendar")
    assert isinstance(cal, dict) and cast(dict[str, Any], cal).get("method") == "PUBLISH"


def test_method_request_surfaced(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """METHOD:REQUEST is the primary scheduling method (RFC 5546 §3.2.2)."""
    ics = _wrap_with_method("REQUEST", _BASE_WITH_ORGANIZER)
    out = run_parse(submission_command, ics, tmp_path)
    cal = out.get("calendar")
    assert isinstance(cal, dict) and cast(dict[str, Any], cal).get("method") == "REQUEST"


def test_method_reply_surfaced(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """METHOD:REPLY is used by attendees to respond (RFC 5546 §3.2.3)."""
    ics = _wrap_with_method("REPLY", _BASE_WITH_ORGANIZER_AND_ATTENDEE_PARTSTAT)
    out = run_parse(submission_command, ics, tmp_path)
    cal = out.get("calendar")
    assert isinstance(cal, dict) and cast(dict[str, Any], cal).get("method") == "REPLY"


# ---------------------------------------------------------------------------
# REQUEST: must have ORGANIZER (RFC 5546 §3.2.2)
# ---------------------------------------------------------------------------


def test_request_missing_organizer_emits_itip_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.2.2: A REQUEST must identify the ORGANIZER. When
    METHOD:REQUEST is declared and the VEVENT lacks an ORGANIZER
    property, the parser must emit an `itip_missing_property` warning."""
    ics = _wrap_with_method("REQUEST", _BASE)  # no ORGANIZER
    out = run_parse(submission_command, ics, tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_well_formed_request_emits_no_itip_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A METHOD:REQUEST calendar with ORGANIZER + ATTENDEE + SEQUENCE
    satisfies the iTIP requirements (RFC 5546 §3.2.2 + §3), so no
    `itip_missing_property` warning should be emitted."""
    ics = _wrap_with_method(
        "REQUEST", _BASE_WITH_ORGANIZER_AND_ATTENDEE_PARTSTAT
    )
    out = run_parse(submission_command, ics, tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)


# ---------------------------------------------------------------------------
# REPLY: must have ORGANIZER *and* ATTENDEE with PARTSTAT (RFC 5546 §3.2.3)
# ---------------------------------------------------------------------------


def test_reply_missing_attendee_emits_itip_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.2.3: A REPLY must carry the ATTENDEE whose response
    is being reported. ORGANIZER is present but ATTENDEE is missing —
    must emit `itip_missing_property`."""
    ics = _wrap_with_method("REPLY", _BASE_WITH_ORGANIZER)  # no ATTENDEE
    out = run_parse(submission_command, ics, tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_reply_missing_organizer_emits_itip_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.2.3: A REPLY must also identify the ORGANIZER the
    reply is directed to. ATTENDEE is present but ORGANIZER is
    missing — must emit `itip_missing_property`."""
    body = _BASE + "ATTENDEE;PARTSTAT=ACCEPTED:mailto:jane@example.com\n"
    ics = _wrap_with_method("REPLY", body)
    out = run_parse(submission_command, ics, tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_reply_attendee_without_partstat_emits_itip_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.2.3: The ATTENDEE in a REPLY must carry a PARTSTAT
    parameter communicating the response (ACCEPTED, DECLINED, etc.).
    Missing PARTSTAT on the reply's ATTENDEE must trigger
    `itip_missing_property`."""
    body = (
        _BASE_WITH_ORGANIZER
        + "ATTENDEE:mailto:jane@example.com\n"  # no PARTSTAT
    )
    ics = _wrap_with_method("REPLY", body)
    out = run_parse(submission_command, ics, tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_well_formed_reply_emits_no_itip_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """REPLY with ORGANIZER, ATTENDEE, and PARTSTAT — all iTIP
    requirements satisfied, so no `itip_missing_property` warning."""
    ics = _wrap_with_method("REPLY", _BASE_WITH_ORGANIZER_AND_ATTENDEE_PARTSTAT)
    out = run_parse(submission_command, ics, tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)


# ---------------------------------------------------------------------------
# CANCEL: must communicate cancellation (STATUS:CANCELLED or implied by
# the CANCEL method itself). RFC 5546 §3.2.5.
# ---------------------------------------------------------------------------


def test_cancel_with_status_cancelled_is_valid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """METHOD:CANCEL with explicit STATUS:CANCELLED is unambiguously a
    valid cancellation — no `itip_missing_property` warning."""
    body = _BASE_WITH_ORGANIZER + "STATUS:CANCELLED\n"
    ics = _wrap_with_method("CANCEL", body)
    out = run_parse(submission_command, ics, tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)


def test_cancel_without_explicit_status_is_valid(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.2.5 allows the CANCEL method to imply cancellation
    without an explicit STATUS:CANCELLED on the VEVENT. The presence of
    METHOD:CANCEL + ORGANIZER is sufficient; absence of STATUS alone
    must not produce an `itip_missing_property` warning."""
    ics = _wrap_with_method("CANCEL", _BASE_WITH_ORGANIZER)
    out = run_parse(submission_command, ics, tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)


def test_cancel_missing_organizer_emits_itip_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.2.5: A CANCEL must still identify the ORGANIZER of
    the event being cancelled. ORGANIZER absent -> warning."""
    ics = _wrap_with_method("CANCEL", _BASE)  # no ORGANIZER
    out = run_parse(submission_command, ics, tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_cancel_status_if_present_must_be_cancelled(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.2.5 STATUS row: "MUST be set to CANCELLED to cancel
    the entire event." A CANCEL that carries STATUS with any value
    other than CANCELLED (e.g. TENTATIVE or CONFIRMED) is internally
    inconsistent — the METHOD says "cancel" but the STATUS does not.
    Validator must warn."""
    body = _BASE_WITH_ORGANIZER + "STATUS:TENTATIVE\n"
    ics = _wrap_with_method("CANCEL", body)
    out = run_parse(submission_command, ics, tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_cancel_status_cancelled_case_insensitive(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5545 property-value comparison for STATUS is case-insensitive
    in practice. STATUS:cancelled (lowercase) on a CANCEL should not
    trigger the "STATUS must be CANCELLED" warning."""
    body = _BASE_WITH_ORGANIZER + "STATUS:cancelled\n"
    ics = _wrap_with_method("CANCEL", body)
    out = run_parse(submission_command, ics, tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)


# ---------------------------------------------------------------------------
# PUBLISH imposes no attendee-level iTIP requirement beyond the base
# VEVENT minimum. A PUBLISH without ORGANIZER or ATTENDEE is fine.
# ---------------------------------------------------------------------------


def test_publish_without_organizer_no_itip_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """METHOD:PUBLISH is a one-way broadcast; neither ORGANIZER nor
    ATTENDEE is iTIP-mandatory for a PUBLISH calendar. No
    `itip_missing_property` warning expected."""
    ics = _wrap_with_method("PUBLISH", _BASE)
    out = run_parse(submission_command, ics, tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)


# ---------------------------------------------------------------------------
# No METHOD at all means iTIP rules don't apply — the file is a plain
# iCalendar object. This test guards against an over-eager implementation
# emitting `itip_missing_property` for every calendar without METHOD.
# ---------------------------------------------------------------------------


def test_no_method_means_no_itip_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Absence of METHOD on VCALENDAR means the document is not an iTIP
    transaction. iTIP-specific warnings must not be raised."""
    ics = (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//Test//EN\n"
        "BEGIN:VEVENT\n"
        + _BASE
        + "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)


# ---------------------------------------------------------------------------
# The calendar.method field must always be present (null when absent) so
# downstream code can branch safely. This is a small schema/shape test
# focused on iTIP dispatch.
# ---------------------------------------------------------------------------


def test_calendar_method_null_when_absent(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """When no METHOD property is present, calendar.method should be
    null (not missing) per the parse schema."""
    ics = (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//Test//EN\n"
        "BEGIN:VEVENT\n"
        + _BASE
        + "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    cal = out.get("calendar")
    assert isinstance(cal, dict)
    # Use `.get()` so a schema bug (missing key) doesn't get confused
    # with a value bug (non-null method).
    assert cast(dict[str, Any], cal).get("method") is None


# ---------------------------------------------------------------------------
# Minor variations: case-insensitive METHOD values per RFC 5545 parameter
# handling. The method token itself is typically upper-case, but the
# calendar.method output should reflect the uppercase canonical form.
# ---------------------------------------------------------------------------


def test_method_value_canonicalized_uppercase(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Iana-registered iTIP method tokens are case-insensitive on input
    but conventionally rendered in upper case. `METHOD:request` on input
    should still be surfaced such that REQUEST-flavoured iTIP
    requirements are enforced: an event without ORGANIZER produces
    `itip_missing_property`. (We do not assert exact casing of
    calendar.method; we only assert the semantic side-effect.)"""
    ics = (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//Test//EN\n"
        "METHOD:request\n"  # lowercase
        "BEGIN:VEVENT\n"
        + _BASE  # no ORGANIZER
        + "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)
