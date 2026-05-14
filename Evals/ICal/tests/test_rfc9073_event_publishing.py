"""RFC 9073 — Event Publishing Extensions to iCalendar (August 2021).

Defines a rich set of additions for publishing structured event data:

  * PARTICIPANT component — distinct from ATTENDEE, carries role-
    based information about anyone involved with the event.
  * VLOCATION sub-component — rich location with hierarchy, type,
    structured address.
  * VRESOURCE sub-component — bookable resource definition.
  * STRUCTURED-DATA property — JSON/XML/URI payload of structured
    event data (e.g., schema.org).
  * STYLED-DESCRIPTION property — formatted description with
    FMTTYPE (text/html, text/markdown).
  * LOCATION-TYPE parameter on LOCATION.

For properties and components we haven't fully typed, the contract
is that `raw_properties` preserves them for downstream processing.
Tests assert preservation at the raw level.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import find_event, run_parse, wrap_event


def _event_with(inner: str, uid: str = "e1") -> str:
    body = f"UID:{uid}\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n{inner}"
    return wrap_event(body)


def _raw_names(ev: dict[str, Any]) -> list[str]:
    raw = cast(list[dict[str, Any]], ev.get("raw_properties") or [])
    return [str(p.get("name", "")).upper() for p in raw]


def _raw_prop(ev: dict[str, Any], name: str) -> dict[str, Any] | None:
    target = name.upper()
    raw = cast(list[dict[str, Any]], ev.get("raw_properties") or [])
    for p in raw:
        if str(p.get("name", "")).upper() == target:
            return p
    return None


# ---------------------------------------------------------------------------
# STRUCTURED-DATA (RFC 9073 §6.6)
# ---------------------------------------------------------------------------


def test_structured_data_uri(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """STRUCTURED-DATA with a URI reference is preserved."""
    ics = _event_with("STRUCTURED-DATA;VALUE=URI:https://example.com/schema-org/event.jsonld\n")
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    assert "STRUCTURED-DATA" in _raw_names(ev)


def test_structured_data_inline_text(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """STRUCTURED-DATA inline TEXT with FMTTYPE=application/json."""
    ics = _event_with(
        "STRUCTURED-DATA;FMTTYPE=application/json;VALUE=TEXT:"
        '{"@context":"https://schema.org"\\,"@type":"Event"}\n'
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    prop = _raw_prop(ev, "STRUCTURED-DATA")
    assert prop is not None
    params = cast(dict[str, Any], prop.get("params", {}))
    assert params.get("FMTTYPE") == "application/json"


def test_structured_data_binary_base64(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = _event_with("STRUCTURED-DATA;ENCODING=BASE64;VALUE=BINARY:aGVsbG8=\n")
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    prop = _raw_prop(ev, "STRUCTURED-DATA")
    assert prop is not None


# ---------------------------------------------------------------------------
# STYLED-DESCRIPTION (RFC 9073 §6.5)
# ---------------------------------------------------------------------------


def test_styled_description_html(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """STYLED-DESCRIPTION with FMTTYPE=text/html."""
    ics = _event_with(
        "STYLED-DESCRIPTION;FMTTYPE=text/html:<p>Rich <b>formatted</b> description</p>\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    prop = _raw_prop(ev, "STYLED-DESCRIPTION")
    assert prop is not None
    params = cast(dict[str, Any], prop.get("params", {}))
    assert params.get("FMTTYPE") == "text/html"


def test_styled_description_markdown(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = _event_with(
        "STYLED-DESCRIPTION;FMTTYPE=text/markdown:# Event Title\\n\\n*Details* here\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    prop = _raw_prop(ev, "STYLED-DESCRIPTION")
    assert prop is not None
    params = cast(dict[str, Any], prop["params"])
    assert params.get("FMTTYPE") == "text/markdown"


def test_styled_description_with_language(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    ics = _event_with(
        "STYLED-DESCRIPTION;FMTTYPE=text/html;LANGUAGE=es:<p>Descripción en espa\xf1ol</p>\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    prop = _raw_prop(ev, "STYLED-DESCRIPTION")
    assert prop is not None
    params = cast(dict[str, Any], prop["params"])
    assert params.get("LANGUAGE") == "es"


def test_multiple_styled_descriptions_for_multilingual(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Multiple STYLED-DESCRIPTION lines are preserved (i18n)."""
    ics = _event_with(
        "STYLED-DESCRIPTION;FMTTYPE=text/html;LANGUAGE=en:<p>English</p>\n"
        "STYLED-DESCRIPTION;FMTTYPE=text/html;LANGUAGE=fr:<p>Français</p>\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    raw = cast(list[dict[str, Any]], ev.get("raw_properties") or [])
    styled = [p for p in raw if str(p.get("name", "")).upper() == "STYLED-DESCRIPTION"]
    assert len(styled) == 2


# ---------------------------------------------------------------------------
# LOCATION-TYPE parameter on LOCATION (RFC 9073 §5.1)
# ---------------------------------------------------------------------------


def test_location_with_location_type(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    ics = _event_with("LOCATION;LOCATION-TYPE=virtual:https://zoom.us/j/123456\n")
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    prop = _raw_prop(ev, "LOCATION")
    assert prop is not None
    assert prop["params"].get("LOCATION-TYPE") == "virtual"


# ---------------------------------------------------------------------------
# PARTICIPANT component (RFC 9073 §7)
# ---------------------------------------------------------------------------


def test_participant_component_is_not_dropped(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """PARTICIPANT is a new sub-component of VEVENT. v1.2 tool may not
    fully type it, but must not crash and should surface an
    unsupported_component warning or preserve it in raw."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:PARTICIPANT\n"
        "UID:p1\n"
        "PARTICIPANT-TYPE:ATTENDEE\n"
        "CALENDAR-ADDRESS:mailto:alice@example.com\n"
        "END:PARTICIPANT\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    # Event must still parse. Warning may be emitted; not enforced.
    events = cast(list[dict[str, Any]], out.get("events") or [])
    assert len(events) == 1
    assert events[0].get("uid") == "e1"


# ---------------------------------------------------------------------------
# VLOCATION sub-component (RFC 9073 §7.2)
# ---------------------------------------------------------------------------


def test_vlocation_component_does_not_crash_parser(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """VLOCATION inside VEVENT."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VLOCATION\n"
        "UID:loc1\n"
        "NAME:Conference Room\n"
        "LOCATION-TYPE:office\n"
        "END:VLOCATION\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    events = cast(list[dict[str, Any]], out.get("events") or [])
    assert len(events) == 1


# ---------------------------------------------------------------------------
# VRESOURCE sub-component (RFC 9073 §7.3)
# ---------------------------------------------------------------------------


def test_vresource_component_does_not_crash_parser(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\n"
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VRESOURCE\n"
        "UID:res1\n"
        "NAME:Projector\n"
        "RESOURCE-TYPE:equipment\n"
        "END:VRESOURCE\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    events = cast(list[dict[str, Any]], out.get("events") or [])
    assert len(events) == 1


def test_known_component_nested_in_unknown_does_not_escape(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A known sub-component (e.g. VALARM) nested inside an unknown outer
    component (e.g. PARTICIPANT) must NOT be opened as a real VALARM. If
    the parent is dropped as unsupported, the nested VALARM is equally
    dropped — it would attach to the wrong scope otherwise."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VEVENT\n"
        "UID:outer-event\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\n"
        "BEGIN:PARTICIPANT\n"
        "UID:p1\n"
        "PARTICIPANT-TYPE:ATTENDEE\n"
        "BEGIN:VALARM\n"
        "ACTION:DISPLAY\n"
        "TRIGGER:-PT15M\n"
        "DESCRIPTION:inner-alarm-should-not-leak\n"
        "END:VALARM\n"
        "END:PARTICIPANT\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    events = cast(list[dict[str, Any]], out.get("events") or [])
    assert len(events) == 1
    # The outer event must keep its own UID, unchanged by nested PARTICIPANT.
    assert events[0].get("uid") == "outer-event"
    # The event's alarms list must be empty: the nested VALARM was inside
    # an unsupported outer PARTICIPANT and should NOT leak to the event.
    alarms = cast(list[Any], events[0].get("alarms") or [])
    assert len(alarms) == 0


# ---------------------------------------------------------------------------
# RFC 9073 component uses alongside standard VEVENT properties
# ---------------------------------------------------------------------------


def test_rfc9073_props_alongside_standard_event(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A realistic VEVENT using several RFC 9073 properties."""
    ics = _event_with(
        "SUMMARY:Community Meetup\n"
        "LOCATION;LOCATION-TYPE=virtual:https://zoom.us/j/999\n"
        "STYLED-DESCRIPTION;FMTTYPE=text/html:<p>Welcome</p>\n"
        "STRUCTURED-DATA;VALUE=URI:https://example.com/event.jsonld\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    names = _raw_names(ev)
    assert "STYLED-DESCRIPTION" in names
    assert "STRUCTURED-DATA" in names
    assert "LOCATION" in names
    # Standard fields still work.
    assert ev.get("summary") == "Community Meetup"


# ---------------------------------------------------------------------------
# CALENDAR-ADDRESS property (RFC 9073 §6.3)
# ---------------------------------------------------------------------------


def test_calendar_address_property_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """CALENDAR-ADDRESS on PARTICIPANT or event is preserved."""
    ics = _event_with("CALENDAR-ADDRESS:mailto:cal@example.com\n")
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    assert "CALENDAR-ADDRESS" in _raw_names(ev)


# ---------------------------------------------------------------------------
# RESOURCE-TYPE parameter values
# ---------------------------------------------------------------------------


def test_resources_parameter_on_vevent(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """RFC 9073 doesn't change RESOURCES itself; ensures RESOURCES-related
    functionality doesn't regress when event also has RFC 9073 props."""
    ics = _event_with(
        "RESOURCES:PROJECTOR,WHITEBOARD\nSTYLED-DESCRIPTION;FMTTYPE=text/html:<p>x</p>\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    assert "PROJECTOR" in cast(list[Any], ev.get("resources") or [])
