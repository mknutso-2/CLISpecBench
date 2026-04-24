"""VALARM semantics per RFC 5545 §3.6.6 (Alarm Component) and §3.8.6.3 (TRIGGER).

Each VEVENT may carry zero or more VALARM subcomponents. Parsed alarms appear
under `event["alarms"]` as a list of valarm objects with the fields:
`action`, `trigger` (an object with `value` and `related`), `description`,
`summary`, `attendees`, `duration`, `repeat`, `attach`, `acknowledged`,
and `raw_properties`.

§3.6.6 constraints exercised here:
  * AUDIO requires ACTION + TRIGGER (ATTACH optional).
  * DISPLAY requires ACTION + TRIGGER + DESCRIPTION.
  * EMAIL requires ACTION + TRIGGER + DESCRIPTION + SUMMARY + >=1 ATTENDEE.
  * DURATION + REPEAT go together; either both or neither.
  * TRIGGER default value type is DURATION (relative).
  * TRIGGER;VALUE=DATE-TIME means an absolute UTC trigger.
  * TRIGGER;RELATED=START (default) or RELATED=END; MUST only appear when
    the value type is DURATION (not DATE-TIME).
  * Multiple independent VALARMs may appear in a single VEVENT.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import find_event, run_parse, wrap_event


def _alarms_of(event: dict[str, Any]) -> list[dict[str, Any]]:
    alarms = event.get("alarms")
    assert isinstance(alarms, list), f"event has no 'alarms' array; got keys {list(event)}"
    return cast(list[dict[str, Any]], alarms)


# --- Shape / presence ---


def test_event_without_alarm_has_empty_alarms_list(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An event with no VALARM yields `alarms: []`, not missing or null."""
    ics = wrap_event(
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\nSUMMARY:noalarm\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    assert _alarms_of(ev) == []


def test_display_alarm_basic_fields(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.6.6 DISPLAY alarm exposes action, trigger.value, description."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VALARM\n"
        "ACTION:DISPLAY\n"
        "TRIGGER:-PT15M\n"
        "DESCRIPTION:Reminder\n"
        "END:VALARM\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    alarms = _alarms_of(find_event(out, "e1"))
    assert len(alarms) == 1
    alarm = alarms[0]
    assert alarm.get("action") == "DISPLAY"
    assert alarm.get("description") == "Reminder"
    trigger_raw = alarm.get("trigger")
    assert isinstance(trigger_raw, dict), "trigger must be an object"
    trigger = cast(dict[str, Any], trigger_raw)
    assert trigger.get("value") == "-PT15M"


# --- TRIGGER: relative vs absolute ---


def test_trigger_default_related_is_start(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.2.14: if RELATED is not specified on a DURATION-valued TRIGGER, default is START."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VALARM\n"
        "ACTION:DISPLAY\n"
        "TRIGGER:-PT30M\n"
        "DESCRIPTION:half hour early\n"
        "END:VALARM\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    trigger_raw = alarm.get("trigger")
    assert isinstance(trigger_raw, dict)
    trigger = cast(dict[str, Any], trigger_raw)
    assert trigger.get("related") == "START"


def test_trigger_related_end_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.2.14: RELATED=END is surfaced on the trigger object."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "DTEND:20260301T110000Z\n"
        "BEGIN:VALARM\n"
        "ACTION:DISPLAY\n"
        "TRIGGER;RELATED=END:PT5M\n"
        "DESCRIPTION:followup\n"
        "END:VALARM\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    trigger_raw = alarm.get("trigger")
    assert isinstance(trigger_raw, dict)
    trigger = cast(dict[str, Any], trigger_raw)
    assert trigger.get("related") == "END"
    assert trigger.get("value") == "PT5M"


def test_trigger_positive_duration_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.8.6.3: positive duration means trigger *after* the anchor."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VALARM\n"
        "ACTION:DISPLAY\n"
        "TRIGGER:PT1H\n"
        "DESCRIPTION:after start\n"
        "END:VALARM\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    # The sign must not be silently dropped.
    assert alarm["trigger"]["value"] == "PT1H"


def test_trigger_absolute_datetime(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.8.6.3: TRIGGER;VALUE=DATE-TIME is absolute UTC. Normalize to ISO-8601."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VALARM\n"
        "ACTION:AUDIO\n"
        "TRIGGER;VALUE=DATE-TIME:20260301T093000Z\n"
        "END:VALARM\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    trigger_raw = alarm.get("trigger")
    assert isinstance(trigger_raw, dict)
    trigger = cast(dict[str, Any], trigger_raw)
    # Normalized ISO-8601 form per the spec's ISO-8601 normalization section.
    assert trigger.get("value") == "2026-03-01T09:30:00Z"
    # §3.8.6.3: "The trigger relationship property parameter MUST only be
    # specified when the value type is DURATION." An absolute trigger thus
    # has no `related`.
    assert trigger.get("related") is None


# --- Actions ---


def test_audio_alarm_action(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.6.6 audioprop: AUDIO is the action, DESCRIPTION is not required."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VALARM\n"
        "ACTION:AUDIO\n"
        "TRIGGER:-PT5M\n"
        "END:VALARM\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    assert alarm["action"] == "AUDIO"
    # No DESCRIPTION supplied → field is absent or null, not a fabricated string.
    assert alarm.get("description") is None


def test_email_alarm_full_fields(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.6.6 emailprop: EMAIL alarm carries summary, description, attendees."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VALARM\n"
        "ACTION:EMAIL\n"
        "TRIGGER:-P1D\n"
        "DESCRIPTION:Body text\n"
        "SUMMARY:Subject text\n"
        "ATTENDEE:mailto:alice@example.com\n"
        "ATTENDEE:mailto:bob@example.com\n"
        "END:VALARM\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    assert alarm["action"] == "EMAIL"
    assert alarm["description"] == "Body text"
    assert alarm["summary"] == "Subject text"
    attendees_raw = alarm.get("attendees")
    assert isinstance(attendees_raw, list)
    attendees = cast(list[dict[str, Any]], attendees_raw)
    assert len(attendees) == 2
    values = {a.get("value") for a in attendees}
    assert values == {"mailto:alice@example.com", "mailto:bob@example.com"}


# --- DURATION / REPEAT pairing ---


def test_duration_and_repeat_together(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.6.6: DURATION and REPEAT both appear => repeating alarm surfaced as-is."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VALARM\n"
        "ACTION:DISPLAY\n"
        "TRIGGER:-PT30M\n"
        "DESCRIPTION:recurring alarm\n"
        "DURATION:PT15M\n"
        "REPEAT:4\n"
        "END:VALARM\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    assert alarm.get("duration") == "PT15M"
    assert alarm.get("repeat") == 4


def test_no_repeat_no_duration(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """If neither DURATION nor REPEAT is present, both fields are null."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VALARM\n"
        "ACTION:DISPLAY\n"
        "TRIGGER:-PT15M\n"
        "DESCRIPTION:one-shot\n"
        "END:VALARM\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    assert alarm.get("duration") is None
    assert alarm.get("repeat") is None


# --- ATTACH on alarms ---


def test_audio_alarm_with_attach(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.6.6 AUDIO may include ATTACH pointing to a sound resource."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VALARM\n"
        "ACTION:AUDIO\n"
        "TRIGGER:-PT10M\n"
        "ATTACH;FMTTYPE=audio/basic:ftp://example.com/sounds/bell.aud\n"
        "END:VALARM\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    attach_raw = alarm.get("attach")
    assert isinstance(attach_raw, list)
    attach = cast(list[dict[str, Any]], attach_raw)
    assert len(attach) == 1
    assert attach[0].get("value") == "ftp://example.com/sounds/bell.aud"
    assert attach[0].get("fmttype") == "audio/basic"


# --- Multiple alarms ---


def test_multiple_alarms_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.6.6: multiple mutually independent VALARMs may appear per VEVENT."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VALARM\n"
        "ACTION:DISPLAY\n"
        "TRIGGER:-PT15M\n"
        "DESCRIPTION:first\n"
        "END:VALARM\n"
        "BEGIN:VALARM\n"
        "ACTION:AUDIO\n"
        "TRIGGER:-PT1H\n"
        "END:VALARM\n"
        "BEGIN:VALARM\n"
        "ACTION:EMAIL\n"
        "TRIGGER:-P1D\n"
        "DESCRIPTION:body\n"
        "SUMMARY:subj\n"
        "ATTENDEE:mailto:alice@example.com\n"
        "END:VALARM\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    alarms = _alarms_of(find_event(out, "e1"))
    assert len(alarms) == 3
    actions = [a.get("action") for a in alarms]
    assert actions == ["DISPLAY", "AUDIO", "EMAIL"]


# --- Acknowledged (RFC 9074, but commonly surfaced) ---


def test_acknowledged_property(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """ACKNOWLEDGED is a DATE-TIME (UTC) tracking last alarm acknowledgement."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VALARM\n"
        "ACTION:DISPLAY\n"
        "TRIGGER:-PT15M\n"
        "DESCRIPTION:x\n"
        "ACKNOWLEDGED:20260301T093000Z\n"
        "END:VALARM\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    # If the implementation surfaces ACKNOWLEDGED, it must be the normalized
    # ISO-8601 UTC form. If the implementation hasn't adopted it, the
    # property still must appear in raw_properties untouched.
    if alarm.get("acknowledged") is not None:
        assert alarm["acknowledged"] == "2026-03-01T09:30:00Z"
    raw_value = alarm.get("raw_properties")
    assert isinstance(raw_value, list)
    raw = cast(list[dict[str, Any]], raw_value)
    names = [p.get("name") for p in raw]
    assert "ACKNOWLEDGED" in [n.upper() if isinstance(n, str) else "" for n in names]


# --- Raw properties preserved ---


def test_alarm_raw_properties_include_action_trigger(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Every alarm property — ACTION, TRIGGER, DESCRIPTION — shows up in raw_properties."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VALARM\n"
        "ACTION:DISPLAY\n"
        "TRIGGER:-PT15M\n"
        "DESCRIPTION:x\n"
        "END:VALARM\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    raw_value = alarm.get("raw_properties")
    assert isinstance(raw_value, list)
    raw = cast(list[dict[str, Any]], raw_value)
    names: set[str] = set()
    for p in raw:
        name = p.get("name")
        if isinstance(name, str):
            names.add(name.upper())
    assert {"ACTION", "TRIGGER", "DESCRIPTION"}.issubset(names)


# --- Alarms on VTODO too ---


def test_alarm_on_vtodo(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.6.6: VALARM MUST only appear within VEVENT or VTODO. Confirm VTODO support."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VTODO\n"
        "UID:t1\nDTSTAMP:20260101T120000Z\n"
        "DUE:20260301T170000Z\n"
        "BEGIN:VALARM\n"
        "ACTION:DISPLAY\n"
        "TRIGGER:-PT30M\n"
        "DESCRIPTION:todo reminder\n"
        "END:VALARM\n"
        "END:VTODO\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    todos_raw = out.get("todos")
    assert isinstance(todos_raw, list)
    todos = cast(list[dict[str, Any]], todos_raw)
    assert len(todos) == 1
    alarms_raw = todos[0].get("alarms")
    assert isinstance(alarms_raw, list)
    alarms = cast(list[dict[str, Any]], alarms_raw)
    assert len(alarms) == 1
    assert alarms[0].get("action") == "DISPLAY"
    trigger = cast(dict[str, Any], alarms[0].get("trigger", {}))
    assert trigger.get("value") == "-PT30M"


# --- Unknown action: x-name / iana-token accepted per §3.6.6 lack of enum ---


def test_non_standard_action_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.6.6 does not enumerate ACTION; implementations should pass through
    the raw token so downstream logic can decide what to do."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "BEGIN:VALARM\n"
        "ACTION:PROCEDURE\n"
        "TRIGGER:-PT5M\n"
        "END:VALARM\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    alarm = _alarms_of(find_event(out, "e1"))[0]
    assert alarm.get("action") == "PROCEDURE"


# --- No ACTION/TRIGGER: malformed (§3.6.6 REQUIRES both) ---


def test_missing_required_alarm_properties_warns(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.6.6: ACTION and TRIGGER are REQUIRED in every VALARM.
    A VALARM missing either should emit a malformed_value warning but should
    NOT abort parsing of the surrounding event."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\nSUMMARY:ok\n"
        "BEGIN:VALARM\n"
        "ACTION:DISPLAY\n"
        # no TRIGGER
        "DESCRIPTION:broken\n"
        "END:VALARM\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(out, "e1")
    # Event itself must still be intact.
    assert ev["summary"] == "ok"
    kinds = [w.get("kind") for w in out.get("warnings", [])]
    assert "malformed_value" in kinds
