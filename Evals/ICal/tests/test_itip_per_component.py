"""RFC 5546 §3.3–§3.5 per-component iTIP validation.

Closes Codex iter 4 adversarial-review finding #P1. Earlier iterations
validated iTIP only against the RFC 5546 §3.2 (VEVENT) matrix, and
reused that matrix for VTODO and VJOURNAL — which is wrong:

  * VJOURNAL (§3.5) only defines PUBLISH / ADD / CANCEL. A REQUEST
    or REFRESH on a VJOURNAL is an RFC violation.
  * VTODO COUNTER (§3.4.7) requires PRIORITY and SUMMARY — neither
    applies to VEVENT COUNTER.
  * VFREEBUSY (§3.3) only defines PUBLISH / REQUEST / REPLY and has
    explicit DTSTART/DTEND/ORGANIZER requirements not inherited from
    any VEVENT table.

These tests exercise the three new per-component matrices. All of
them assert on the `itip_missing_property` warning kind (same kind
for every iTIP rule violation; the message differentiates them).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

from conftest import run_parse

HEAD = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
TAIL = "END:VCALENDAR\n"


def _warn_kinds(out: dict[str, Any]) -> list[str]:
    raw = out.get("warnings") or []
    if not isinstance(raw, list):
        return []
    return [w.get("kind", "") for w in cast(list[dict[str, Any]], raw)]


def _warn_messages(out: dict[str, Any]) -> list[str]:
    raw = out.get("warnings") or []
    if not isinstance(raw, list):
        return []
    return [w.get("message", "") for w in cast(list[dict[str, Any]], raw)]


_ALL_ITIP_PROPERTY_TOKENS = (
    "UID", "DTSTAMP", "DTSTART", "DTEND", "ORGANIZER", "ATTENDEE",
    "SEQUENCE", "SUMMARY", "PRIORITY", "DESCRIPTION", "STATUS",
    "PARTSTAT",
)

# Compile once: token-boundary regex for each property identifier.
# We use a NEGATIVE look-around for ``[\w-]`` on both sides rather
# than Python's built-in ``\b``. The built-in is wrong here because
# ``-`` counts as a NON-word character, so ``\bPRIORITY\b`` still
# matches inside ``X-PRIORITY`` (hyphen-word boundary is a ``\b``
# match point). Real RFC 5545 property names can start with ``X-``
# for vendor extensions, and we want those to be rejected as
# property-token hits. The custom lookaround treats both underscore
# (``_``) and hyphen (``-``) as token-continuation chars.
_TOKEN_RES: dict[str, re.Pattern[str]] = {
    tok: re.compile(r"(?<![\w-])" + tok + r"(?![\w-])")
    for tok in _ALL_ITIP_PROPERTY_TOKENS
}


def _warn_mentions_method_component_property(
    messages: list[str], method: str, component: str, property_name: str
) -> bool:
    """Check the non-VEVENT iTIP warning contract per
    technical-requirements-prompt.md §Warning-schema. A conforming
    message MUST:

      1. Contain the adjacent two-word phrase ``<METHOD> <COMPONENT>``
         OR ``<COMPONENT> <METHOD>`` (single ASCII space between).
      2. Contain the specific RFC property name token under test, as
         a word-boundary-delimited whole word (so ``X-PRIORITY`` or
         ``GUID`` do NOT count as PRIORITY / UID hits).
      3. Contain EXACTLY ONE property token from the allowed list —
         this rules out the "omnibus message" failure mode where a
         single warning lists every possible required property and
         would spuriously satisfy every property-specific test
         (one warning per missing rule, not one warning per
         component×method cell).

    Returns True if at least one message in `messages` satisfies all
    three conditions for the given (method, component, property_name).
    """
    pair_a = f"{method} {component}"
    pair_b = f"{component} {method}"
    target_re = _TOKEN_RES[property_name]
    for m in messages:
        # Rule 1: adjacent phrase, either order.
        if pair_a not in m and pair_b not in m:
            continue
        # Rule 2: the specific property under test must appear as a
        # whole word (not a substring of a longer ident like X-PRIORITY).
        if not target_re.search(m):
            continue
        # Rule 3: exactly one property token in the message overall.
        token_hits = sum(1 for rx in _TOKEN_RES.values() if rx.search(m))
        if token_hits != 1:
            continue
        return True
    return False


# ---------------------------------------------------------------------------
# VJOURNAL §3.5 — only PUBLISH / ADD / CANCEL
# ---------------------------------------------------------------------------


def _vjournal_calendar(method: str, journal_body: str) -> str:
    return (
        HEAD
        + f"METHOD:{method}\n"
        + "BEGIN:VJOURNAL\n"
        + journal_body
        + "END:VJOURNAL\n"
        + TAIL
    )


def test_vjournal_request_is_undefined_method(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.5 does not define REQUEST for VJOURNAL. Emitting
    METHOD:REQUEST on a VJOURNAL-bearing calendar MUST warn. Per
    the warning contract in tech-reqs, undefined-method messages
    only need the component name as a substring — the method name
    is optional for that message variant — so we only require
    `"VJOURNAL"` here."""
    body = (
        "UID:j1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nSUMMARY:Entry\n"
        "ORGANIZER:mailto:boss@example.com\n"
    )
    out = run_parse(submission_command, _vjournal_calendar("REQUEST", body), tmp_path)
    msgs = _warn_messages(out)
    assert any("VJOURNAL" in m for m in msgs), (
        f"expected a warning mentioning VJOURNAL; got {msgs!r}"
    )


def test_vjournal_refresh_is_undefined_method(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Same rule for REFRESH — not in the §3.5 table. Fixture
    carries DTSTART, ORGANIZER, and DESCRIPTION so if the impl
    were to fall back to PUBLISH-style validation, it would
    emit no property-missing warnings. The warning that fires
    must therefore include the "not defined" wording.

    Note: `itip_missing_property` is the warning kind for BOTH
    missing-property and undefined-method cases — the method
    name and "not defined" in the message differentiate them.
    We check the message text here to isolate the
    undefined-method path."""
    body = (
        "UID:j1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nDESCRIPTION:Retro notes\n"
        "ORGANIZER:mailto:boss@example.com\n"
    )
    out = run_parse(submission_command, _vjournal_calendar("REFRESH", body), tmp_path)
    msgs = _warn_messages(out)
    assert any("VJOURNAL" in m and "not defined" in m for m in msgs), (
        f"expected a 'not defined for VJOURNAL' warning; got {msgs!r}"
    )


def test_vjournal_publish_requires_organizer(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.5.1 PUBLISH VJOURNAL ORGANIZER row is `1`. Missing
    ORGANIZER on a PUBLISH VJOURNAL is a matrix violation."""
    body = (
        "UID:j1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nDESCRIPTION:Hello\n"
        # deliberately missing ORGANIZER
    )
    out = run_parse(submission_command, _vjournal_calendar("PUBLISH", body), tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_vjournal_publish_with_organizer_ok(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A PUBLISH VJOURNAL with every §3.5.1 "1" row present
    (DESCRIPTION, DTSTAMP, DTSTART, ORGANIZER, UID) and no ATTENDEE
    is a minimally valid §3.5.1 PUBLISH — no warnings expected."""
    body = (
        "UID:j1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nDESCRIPTION:Hello\n"
        "ORGANIZER:mailto:boss@example.com\n"
    )
    out = run_parse(submission_command, _vjournal_calendar("PUBLISH", body), tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)


def test_vjournal_add_requires_sequence_greater_than_zero(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.5.2: SEQUENCE | 1 with comment `MUST be greater
    than 0.`"""
    body = (
        "UID:j1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nDESCRIPTION:Hello\n"
        "ORGANIZER:mailto:boss@example.com\nSEQUENCE:0\n"
    )
    out = run_parse(submission_command, _vjournal_calendar("ADD", body), tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_vjournal_publish_requires_description(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.5.1 DESCRIPTION row is `1`. Iter 5 review flagged
    that the prior VJOURNAL validator never checked DESCRIPTION."""
    body = (
        "UID:j1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
        # deliberately missing DESCRIPTION
    )
    out = run_parse(submission_command, _vjournal_calendar("PUBLISH", body), tmp_path)
    msgs = _warn_messages(out)
    assert _warn_mentions_method_component_property(
        msgs, "PUBLISH", "VJOURNAL", "DESCRIPTION"
    ), msgs


def test_vjournal_publish_requires_dtstart(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.5.1 DTSTART row is `1`."""
    body = (
        "UID:j1\nDTSTAMP:20260101T120000Z\nDESCRIPTION:Entry body\n"
        "ORGANIZER:mailto:boss@example.com\n"
        # deliberately missing DTSTART
    )
    out = run_parse(submission_command, _vjournal_calendar("PUBLISH", body), tmp_path)
    msgs = _warn_messages(out)
    assert _warn_mentions_method_component_property(msgs, "PUBLISH", "VJOURNAL", "DTSTART"), msgs


def test_vjournal_add_requires_description_and_dtstart(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.5.2 both DESCRIPTION and DTSTART rows are `1`."""
    body = (
        "UID:j1\nDTSTAMP:20260101T120000Z\n"
        "ORGANIZER:mailto:boss@example.com\nSEQUENCE:1\n"
        # deliberately missing DESCRIPTION AND DTSTART
    )
    out = run_parse(submission_command, _vjournal_calendar("ADD", body), tmp_path)
    msgs = _warn_messages(out)
    assert _warn_mentions_method_component_property(msgs, "ADD", "VJOURNAL", "DESCRIPTION"), msgs
    assert _warn_mentions_method_component_property(msgs, "ADD", "VJOURNAL", "DTSTART"), msgs


# ---------------------------------------------------------------------------
# VTODO §3.4 — full matrix with distinctions from VEVENT
# ---------------------------------------------------------------------------


def _vtodo_calendar(method: str, todo_body: str) -> str:
    return (
        HEAD
        + f"METHOD:{method}\n"
        + "BEGIN:VTODO\n"
        + todo_body
        + "END:VTODO\n"
        + TAIL
    )


def test_vtodo_counter_requires_priority(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.4.7 COUNTER VTODO PRIORITY row is `1`. A VTODO
    COUNTER without PRIORITY is a matrix violation — this is a VTODO-
    specific rule not present on VEVENT COUNTER. Warning MUST carry
    the `COUNTER VTODO` adjacent phrase plus the PRIORITY property
    token per the warning contract."""
    body = (
        "UID:t1\nDTSTAMP:20260101T120000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
        "ATTENDEE;PARTSTAT=TENTATIVE:mailto:a@example.com\n"
        "SUMMARY:Alt proposal\n"
        # deliberately missing PRIORITY
    )
    out = run_parse(submission_command, _vtodo_calendar("COUNTER", body), tmp_path)
    msgs = _warn_messages(out)
    assert _warn_mentions_method_component_property(
        msgs, "COUNTER", "VTODO", "PRIORITY"
    ), msgs


def test_vtodo_counter_requires_summary(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.4.7 COUNTER VTODO SUMMARY row is `1`."""
    body = (
        "UID:t1\nDTSTAMP:20260101T120000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
        "ATTENDEE;PARTSTAT=TENTATIVE:mailto:a@example.com\n"
        "PRIORITY:5\n"
        # deliberately missing SUMMARY
    )
    out = run_parse(submission_command, _vtodo_calendar("COUNTER", body), tmp_path)
    msgs = _warn_messages(out)
    assert _warn_mentions_method_component_property(
        msgs, "COUNTER", "VTODO", "SUMMARY"
    ), msgs


def test_vtodo_counter_with_priority_and_summary_ok(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A well-formed COUNTER VTODO with ORGANIZER, ATTENDEE, PRIORITY,
    and SUMMARY must NOT emit the matrix warning."""
    body = (
        "UID:t1\nDTSTAMP:20260101T120000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
        "ATTENDEE;PARTSTAT=TENTATIVE:mailto:a@example.com\n"
        "PRIORITY:5\nSUMMARY:Alternate due date\n"
    )
    out = run_parse(submission_command, _vtodo_calendar("COUNTER", body), tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)


def test_vtodo_publish_requires_organizer(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """VTODO PUBLISH §3.4.1 ORGANIZER row is `1`. Fixture carries every
    OTHER "1" row (DTSTART, PRIORITY, SUMMARY) so the emitted warning
    isolates the ORGANIZER rule. A fixture missing multiple required
    rows can't prove the ORGANIZER check specifically."""
    body = (
        "UID:t1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nPRIORITY:5\nSUMMARY:Task\n"
        # deliberately missing ORGANIZER — all other required rows present
    )
    out = run_parse(submission_command, _vtodo_calendar("PUBLISH", body), tmp_path)
    msgs = _warn_messages(out)
    assert _warn_mentions_method_component_property(msgs, "PUBLISH", "VTODO", "ORGANIZER"), (
        f"expected an isolated ORGANIZER warning on VTODO PUBLISH; got {msgs!r}"
    )


def test_vtodo_publish_requires_priority(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.4.1 VTODO PUBLISH PRIORITY row is `1`. Missing
    PRIORITY on VTODO PUBLISH is a matrix violation — this is a
    VTODO-specific rule not present on VEVENT PUBLISH."""
    body = (
        "UID:t1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nSUMMARY:Task\n"
        "ORGANIZER:mailto:boss@example.com\n"
        # missing PRIORITY
    )
    out = run_parse(submission_command, _vtodo_calendar("PUBLISH", body), tmp_path)
    msgs = _warn_messages(out)
    assert _warn_mentions_method_component_property(msgs, "PUBLISH", "VTODO", "PRIORITY"), (
        f"expected PRIORITY warning on VTODO PUBLISH; got {msgs!r}"
    )


def test_vtodo_request_requires_priority_and_summary(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.4.2 VTODO REQUEST: PRIORITY 1, SUMMARY 1, DTSTART 1.
    Iter 5 adversarial review flagged that VEVENT REQUEST doesn't
    require PRIORITY/SUMMARY but VTODO REQUEST does — so the
    per-component validators must diverge here."""
    body = (
        "UID:t1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
        "ATTENDEE;PARTSTAT=NEEDS-ACTION:mailto:a@example.com\n"
        # deliberately missing PRIORITY AND SUMMARY
    )
    out = run_parse(submission_command, _vtodo_calendar("REQUEST", body), tmp_path)
    msgs = _warn_messages(out)
    assert _warn_mentions_method_component_property(msgs, "REQUEST", "VTODO", "PRIORITY"), msgs
    assert _warn_mentions_method_component_property(msgs, "REQUEST", "VTODO", "SUMMARY"), msgs


# ---------------------------------------------------------------------------
# VFREEBUSY §3.3 — only PUBLISH / REQUEST / REPLY, DTSTART/DTEND required
# ---------------------------------------------------------------------------


def _vfreebusy_calendar(method: str, fb_body: str) -> str:
    return (
        HEAD
        + f"METHOD:{method}\n"
        + "BEGIN:VFREEBUSY\n"
        + fb_body
        + "END:VFREEBUSY\n"
        + TAIL
    )


def test_vfreebusy_cancel_is_undefined_method(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.3 does not define CANCEL for VFREEBUSY."""
    body = (
        "UID:f1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T000000Z\nDTEND:20260302T000000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
    )
    out = run_parse(submission_command, _vfreebusy_calendar("CANCEL", body), tmp_path)
    msgs = _warn_messages(out)
    assert any("VFREEBUSY" in m for m in msgs)


def test_vfreebusy_request_requires_attendee(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5546 §3.3.2: VFREEBUSY REQUEST ATTENDEE row is `1+`."""
    body = (
        "UID:f1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T000000Z\nDTEND:20260302T000000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
        # deliberately missing ATTENDEE
    )
    out = run_parse(submission_command, _vfreebusy_calendar("REQUEST", body), tmp_path)
    assert "itip_missing_property" in _warn_kinds(out)


def test_vfreebusy_publish_requires_dtstart_and_dtend(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """All three VFREEBUSY iTIP methods require DTSTART and DTEND
    (§3.3.1/§3.3.2/§3.3.3 tables). Missing DTEND on a PUBLISH is a
    matrix violation. Per the warning contract, the message MUST
    carry the adjacent two-word phrase `PUBLISH VFREEBUSY` (or
    `VFREEBUSY PUBLISH`) plus the property name, with at most one
    property token in the message — earlier impls emitted
    `"VFREEBUSY iTIP requires DTEND"` without the method name, which
    violated the contract."""
    body = (
        "UID:f1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T000000Z\n"  # no DTEND
        "ORGANIZER:mailto:boss@example.com\n"
    )
    out = run_parse(submission_command, _vfreebusy_calendar("PUBLISH", body), tmp_path)
    msgs = _warn_messages(out)
    assert _warn_mentions_method_component_property(msgs, "PUBLISH", "VFREEBUSY", "DTEND"), msgs


def test_vfreebusy_shared_check_messages_carry_adjacent_phrase(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """The universal UID/DTSTAMP/ORGANIZER checks on VFREEBUSY must
    ALSO include the method-plus-component adjacent phrase per the
    warning contract. Prior impls emitted bare
    `"iTIP message requires UID"` — no method, no component — which
    left tests unable to discriminate a missing-UID on a VFREEBUSY
    from a missing-UID on any other component.

    Fixture: empty UID + no DTSTAMP on a REQUEST VFREEBUSY. Both
    warnings MUST contain the adjacent phrase `REQUEST VFREEBUSY`
    (or `VFREEBUSY REQUEST`) plus exactly one property token."""
    body = (
        # UID intentionally empty (trailing value),  no DTSTAMP.
        "UID:\n"
        "DTSTART:20260301T000000Z\nDTEND:20260302T000000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
        "ATTENDEE:mailto:a@example.com\n"
    )
    out = run_parse(submission_command, _vfreebusy_calendar("REQUEST", body), tmp_path)
    msgs = _warn_messages(out)
    assert _warn_mentions_method_component_property(msgs, "REQUEST", "VFREEBUSY", "UID"), msgs
    assert _warn_mentions_method_component_property(msgs, "REQUEST", "VFREEBUSY", "DTSTAMP"), msgs


def test_vfreebusy_publish_forbids_attendee(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """VFREEBUSY PUBLISH §3.3.1 ATTENDEE row is `0` (MUST NOT)."""
    body = (
        "UID:f1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T000000Z\nDTEND:20260302T000000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
        "ATTENDEE:mailto:a@example.com\n"  # MUST NOT be present
    )
    out = run_parse(submission_command, _vfreebusy_calendar("PUBLISH", body), tmp_path)
    msgs = _warn_messages(out)
    assert _warn_mentions_method_component_property(msgs, "PUBLISH", "VFREEBUSY", "ATTENDEE"), msgs


def test_vfreebusy_publish_well_formed_ok(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Minimally valid VFREEBUSY PUBLISH: UID, DTSTAMP, DTSTART, DTEND,
    ORGANIZER, no ATTENDEE."""
    body = (
        "UID:f1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T000000Z\nDTEND:20260302T000000Z\n"
        "ORGANIZER:mailto:boss@example.com\n"
    )
    out = run_parse(submission_command, _vfreebusy_calendar("PUBLISH", body), tmp_path)
    assert "itip_missing_property" not in _warn_kinds(out)
