"""RFC 9074 ``VALARM`` Extensions.

RFC 9074 (August 2021) updates RFC 5545 §3.6.6 with:

  * ``UID`` — required-ish inside VALARM for cross-replica identity.
  * ``ACKNOWLEDGED`` — UTC DATE-TIME of last user acknowledgement.
  * ``PROXIMITY`` — location-based trigger hint (``ARRIVE`` | ``DEPART``
    | x-name).
  * ``RELATED-TO`` — links this VALARM to another component (event or
    alarm) with optional ``RELTYPE``.
  * Enhanced EMAIL-alarm semantics.

The ``test_valarm.py`` file in this eval covers the RFC 5545 core. This
file deepens coverage to the RFC 9074 extensions shipped under
``prompt/docs/authoritative/rfc9074.txt``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import find_event, run_parse, wrap_event


def _alarms_of(ev: dict[str, Any]) -> list[dict[str, Any]]:
    raw = ev.get("alarms")
    assert isinstance(raw, list), f"event missing alarms array; got {list(ev)}"
    return cast(list[dict[str, Any]], raw)


def _wrap_alarm(properties: str) -> str:
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VALARM\n" + properties + "END:VALARM\n"
    )
    return wrap_event(body)


# ---------------------------------------------------------------------------
# UID on VALARM (RFC 9074 §4)
# ---------------------------------------------------------------------------


def test_valarm_uid_preserved(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """RFC 9074 §4: UID may appear inside VALARM for cross-replica identity."""
    body = "UID:alarm-xyz-123\nACTION:DISPLAY\nTRIGGER:-PT15M\nDESCRIPTION:X\n"
    ics = _wrap_alarm(body)
    out = run_parse(submission_command, ics, tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    # uid is optional; if the tool surfaces it, it must match.
    if "uid" in alarm:
        assert alarm["uid"] == "alarm-xyz-123"
    # Either way, raw_properties should carry it.
    raw = cast(list[dict[str, Any]], alarm.get("raw_properties") or [])
    names = [str(p.get("name", "")).upper() for p in raw]
    assert "UID" in names, f"UID not in raw_properties: {names}"


# ---------------------------------------------------------------------------
# ACKNOWLEDGED (RFC 9074 §6)
# ---------------------------------------------------------------------------


def test_acknowledged_absolute_datetime(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 9074 §6: ACKNOWLEDGED is a UTC DATE-TIME of last ack."""
    body = "ACTION:DISPLAY\nTRIGGER:-PT15M\nDESCRIPTION:X\nACKNOWLEDGED:20260301T090500Z\n"
    ics = _wrap_alarm(body)
    out = run_parse(submission_command, ics, tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    ack = alarm.get("acknowledged")
    assert ack is not None
    # Per the schema, ISO-8601 UTC form with trailing Z.
    assert isinstance(ack, str) and ack.endswith("Z")
    assert "2026-03-01" in ack


def test_acknowledged_absence_is_null(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """If ACKNOWLEDGED is not present, acknowledged is null."""
    body = "ACTION:DISPLAY\nTRIGGER:-PT15M\nDESCRIPTION:X\n"
    ics = _wrap_alarm(body)
    out = run_parse(submission_command, ics, tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    assert alarm.get("acknowledged") in (None, "")


# ---------------------------------------------------------------------------
# PROXIMITY (RFC 9074 §8)
# ---------------------------------------------------------------------------


def test_proximity_arrive(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """RFC 9074 §8: PROXIMITY=ARRIVE."""
    body = "ACTION:DISPLAY\nTRIGGER:-PT15M\nDESCRIPTION:X\nPROXIMITY:ARRIVE\n"
    ics = _wrap_alarm(body)
    out = run_parse(submission_command, ics, tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    assert alarm.get("proximity") == "ARRIVE"


def test_proximity_depart(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = "ACTION:DISPLAY\nTRIGGER:-PT15M\nDESCRIPTION:X\nPROXIMITY:DEPART\n"
    ics = _wrap_alarm(body)
    out = run_parse(submission_command, ics, tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    assert alarm.get("proximity") == "DEPART"


def test_proximity_xname_preserved(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """x-name PROXIMITY values are preserved as strings, not coerced."""
    body = "ACTION:DISPLAY\nTRIGGER:-PT15M\nDESCRIPTION:X\nPROXIMITY:X-CUSTOM-ZONE\n"
    ics = _wrap_alarm(body)
    out = run_parse(submission_command, ics, tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    # tech-reqs declares `proximity: ARRIVE | DEPART | string | null`
    # — the `string` arm covers x-names. The emitted value MUST be
    # the literal X-CUSTOM-ZONE string; null would silently drop the
    # x-name and require consumers to sift raw_properties to find it.
    assert alarm.get("proximity") == "X-CUSTOM-ZONE"


def test_proximity_absence_is_null(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = "ACTION:DISPLAY\nTRIGGER:-PT15M\nDESCRIPTION:X\n"
    ics = _wrap_alarm(body)
    out = run_parse(submission_command, ics, tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    assert alarm.get("proximity") in (None, "")


# ---------------------------------------------------------------------------
# RELATED-TO (RFC 9074 §9)
# ---------------------------------------------------------------------------


def test_related_to_plain_uid(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """RFC 9074 §9: RELATED-TO value is a UID string; default RELTYPE=PARENT."""
    body = "ACTION:DISPLAY\nTRIGGER:-PT15M\nDESCRIPTION:X\nRELATED-TO:other-event-uid\n"
    ics = _wrap_alarm(body)
    out = run_parse(submission_command, ics, tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    rels = cast(list[dict[str, Any]], alarm.get("related_to") or [])
    assert any(r.get("value") == "other-event-uid" for r in rels), (
        f"related_to missing 'other-event-uid'; got {rels!r}"
    )


def test_related_to_with_reltype(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """RELTYPE parameter: PARENT / CHILD / SIBLING / x-name."""
    body = (
        "ACTION:DISPLAY\nTRIGGER:-PT15M\nDESCRIPTION:X\n"
        "RELATED-TO;RELTYPE=SIBLING:sibling-alarm-uid\n"
    )
    ics = _wrap_alarm(body)
    out = run_parse(submission_command, ics, tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    rels = cast(list[dict[str, Any]], alarm.get("related_to") or [])
    sibling = next((r for r in rels if r.get("value") == "sibling-alarm-uid"), None)
    assert sibling is not None
    if "reltype" in sibling:
        assert sibling["reltype"] == "SIBLING"


def test_related_to_multiple_entries(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """Multiple RELATED-TO properties accumulate."""
    body = (
        "ACTION:DISPLAY\nTRIGGER:-PT15M\nDESCRIPTION:X\n"
        "RELATED-TO:parent-uid\n"
        "RELATED-TO;RELTYPE=CHILD:child-uid\n"
    )
    ics = _wrap_alarm(body)
    out = run_parse(submission_command, ics, tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    rels = cast(list[dict[str, Any]], alarm.get("related_to") or [])
    values = [r.get("value") for r in rels]
    assert "parent-uid" in values
    assert "child-uid" in values


# ---------------------------------------------------------------------------
# Snooze workflow: REPEAT + DURATION + ACKNOWLEDGED
# ---------------------------------------------------------------------------


def test_snooze_via_repeat_and_acknowledged(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 9074 §6: snooze is implemented as REPEAT + DURATION with
    ACKNOWLEDGED tracking which repetition the user last dismissed."""
    body = (
        "ACTION:DISPLAY\nTRIGGER:-PT15M\nDESCRIPTION:X\n"
        "REPEAT:3\nDURATION:PT5M\n"
        "ACKNOWLEDGED:20260301T095500Z\n"
    )
    ics = _wrap_alarm(body)
    out = run_parse(submission_command, ics, tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    assert alarm.get("repeat") == 3
    assert alarm.get("duration") is not None
    assert alarm.get("acknowledged") is not None


# ---------------------------------------------------------------------------
# raw_properties on VALARM preserves RFC 9074 props
# ---------------------------------------------------------------------------


def test_rfc9074_properties_in_raw_even_if_unfielded(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Even if the tool doesn't normalize every RFC 9074 property to a
    typed field, the raw_properties array must carry them."""
    body = (
        "ACTION:DISPLAY\nTRIGGER:-PT15M\nDESCRIPTION:X\n"
        "PROXIMITY:ARRIVE\n"
        "RELATED-TO:x\n"
        "ACKNOWLEDGED:20260301T090500Z\n"
    )
    ics = _wrap_alarm(body)
    out = run_parse(submission_command, ics, tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    raw = cast(list[dict[str, Any]], alarm.get("raw_properties") or [])
    names = [str(p.get("name", "")).upper() for p in raw]
    # All three RFC 9074 property names must appear in raw_properties.
    for n in ("PROXIMITY", "RELATED-TO", "ACKNOWLEDGED"):
        assert n in names, f"{n} missing from raw_properties; got {names}"
