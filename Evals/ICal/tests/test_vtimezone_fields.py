"""VTIMEZONE-level fields and duplicate-UID detection.

Codex v1.0 adversarial-review finding #2 continued. The schema
promised VTIMEZONE `last_modified` / `tzurl` / `comment`, and warning
kinds including `duplicate_uid`. These were previously unimplemented.

References:
  * RFC 5545 §3.8.7.3 LAST-MODIFIED (applicable to VTIMEZONE).
  * RFC 5545 §3.8.3.5 TZURL.
  * RFC 5545 §3.8.1.4 COMMENT (may repeat).
  * RFC 5545 §3.8.4.7 UID uniqueness.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import run_parse

VCALENDAR_HEAD = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
VCALENDAR_TAIL = "END:VCALENDAR\n"


def _wrap_tz(body: str) -> str:
    return VCALENDAR_HEAD + "BEGIN:VTIMEZONE\n" + body + "END:VTIMEZONE\n" + VCALENDAR_TAIL


def _tzs(out: dict[str, Any]) -> list[dict[str, Any]]:
    raw = out.get("timezones")
    assert isinstance(raw, list)
    return cast(list[dict[str, Any]], raw)


# ---------------------------------------------------------------------------
# LAST-MODIFIED on VTIMEZONE (§3.8.7.3)
# ---------------------------------------------------------------------------


def test_vtimezone_last_modified(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "TZID:America/New_York\n"
        "LAST-MODIFIED:20230115T120000Z\n"
        "BEGIN:STANDARD\n"
        "DTSTART:20231105T020000\n"
        "TZOFFSETFROM:-0400\nTZOFFSETTO:-0500\n"
        "END:STANDARD\n"
    )
    out = run_parse(submission_command, _wrap_tz(body), tmp_path)
    tzs = _tzs(out)
    assert len(tzs) == 1
    lm = tzs[0].get("last_modified")
    assert isinstance(lm, str) and "2023-01-15" in lm
    assert lm.endswith("Z")


def test_vtimezone_last_modified_absence_is_null(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "TZID:Etc/UTC\n"
        "BEGIN:STANDARD\n"
        "DTSTART:19700101T000000\n"
        "TZOFFSETFROM:+0000\nTZOFFSETTO:+0000\n"
        "END:STANDARD\n"
    )
    out = run_parse(submission_command, _wrap_tz(body), tmp_path)
    tzs = _tzs(out)
    assert tzs[0].get("last_modified") is None


# ---------------------------------------------------------------------------
# TZURL (§3.8.3.5)
# ---------------------------------------------------------------------------


def test_vtimezone_tzurl(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = (
        "TZID:America/Los_Angeles\n"
        "TZURL:http://tz.example.com/tz/America/Los_Angeles\n"
        "BEGIN:STANDARD\n"
        "DTSTART:20071104T020000\n"
        "TZOFFSETFROM:-0700\nTZOFFSETTO:-0800\n"
        "END:STANDARD\n"
    )
    out = run_parse(submission_command, _wrap_tz(body), tmp_path)
    tzs = _tzs(out)
    assert tzs[0].get("tzurl") == "http://tz.example.com/tz/America/Los_Angeles"


# ---------------------------------------------------------------------------
# COMMENT (§3.8.1.4) — can repeat
# ---------------------------------------------------------------------------


def test_vtimezone_single_comment(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "TZID:Europe/Berlin\n"
        "COMMENT:Data from IANA tzdata 2024a\n"
        "BEGIN:STANDARD\n"
        "DTSTART:19701025T030000\n"
        "TZOFFSETFROM:+0200\nTZOFFSETTO:+0100\n"
        "END:STANDARD\n"
    )
    out = run_parse(submission_command, _wrap_tz(body), tmp_path)
    tzs = _tzs(out)
    comments = cast(list[Any], tzs[0].get("comment") or [])
    assert len(comments) == 1
    assert "IANA" in cast(str, comments[0])


def test_vtimezone_multiple_comments(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "TZID:Europe/Berlin\n"
        "COMMENT:Source\\: tzdata 2024a\n"
        "COMMENT:Regenerated 2024-06-01\n"
        "BEGIN:STANDARD\n"
        "DTSTART:19701025T030000\n"
        "TZOFFSETFROM:+0200\nTZOFFSETTO:+0100\n"
        "END:STANDARD\n"
    )
    out = run_parse(submission_command, _wrap_tz(body), tmp_path)
    tzs = _tzs(out)
    comments = cast(list[Any], tzs[0].get("comment") or [])
    assert len(comments) == 2


def test_vtimezone_absence_is_empty_comment_list(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "TZID:Etc/UTC\n"
        "BEGIN:STANDARD\n"
        "DTSTART:19700101T000000\n"
        "TZOFFSETFROM:+0000\nTZOFFSETTO:+0000\n"
        "END:STANDARD\n"
    )
    out = run_parse(submission_command, _wrap_tz(body), tmp_path)
    tzs = _tzs(out)
    assert tzs[0].get("comment") == []


# ---------------------------------------------------------------------------
# duplicate_uid warning (§3.8.4.7)
# ---------------------------------------------------------------------------


def test_duplicate_uid_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Two non-override events sharing UID → duplicate_uid warning."""
    ics = (
        VCALENDAR_HEAD
        + "BEGIN:VEVENT\nUID:same-uid\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nEND:VEVENT\n"
        + "BEGIN:VEVENT\nUID:same-uid\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260302T100000Z\nEND:VEVENT\n"
        + VCALENDAR_TAIL
    )
    out = run_parse(submission_command, ics, tmp_path)
    warnings = cast(list[dict[str, Any]], out.get("warnings") or [])
    kinds = [w.get("kind") for w in warnings]
    assert "duplicate_uid" in kinds


def test_override_same_uid_does_not_warn_duplicate(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A base event + an override event sharing UID should NOT warn
    `duplicate_uid` — overrides are expected to share UID with their base."""
    ics = (
        VCALENDAR_HEAD
        + "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "RRULE:FREQ=DAILY;COUNT=3\nEND:VEVENT\n"
        + "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260101T120000Z\n"
        "RECURRENCE-ID:20260302T100000Z\nDTSTART:20260302T150000Z\nEND:VEVENT\n"
        + VCALENDAR_TAIL
    )
    out = run_parse(submission_command, ics, tmp_path)
    warnings = cast(list[dict[str, Any]], out.get("warnings") or [])
    kinds = [w.get("kind") for w in warnings]
    assert "duplicate_uid" not in kinds


def test_unique_uids_no_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    ics = (
        VCALENDAR_HEAD
        + "BEGIN:VEVENT\nUID:a\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\nEND:VEVENT\n"
        + "BEGIN:VEVENT\nUID:b\nDTSTAMP:20260101T120000Z\nDTSTART:20260302T100000Z\nEND:VEVENT\n"
        + VCALENDAR_TAIL
    )
    out = run_parse(submission_command, ics, tmp_path)
    warnings = cast(list[dict[str, Any]], out.get("warnings") or [])
    kinds = [w.get("kind") for w in warnings]
    assert "duplicate_uid" not in kinds
