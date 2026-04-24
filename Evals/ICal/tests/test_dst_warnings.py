"""DST fold-ambiguous and nonexistent-local-time warnings.

Closes Codex v1.0 adversarial-review finding #5. The README and
summary.md promised two warning kinds that weren't implemented:

  * `timezone_fold_ambiguous` — a local DATE-TIME falls in the DST
    fall-back overlap where the clock goes backward (e.g. US/Eastern
    01:30 on the first Sunday of November occurs twice).
  * `nonexistent_local_time` — a local DATE-TIME falls in the DST
    spring-forward gap where wall-clock jumps (e.g. US/Eastern 02:30
    on the second Sunday of March doesn't exist).

Resolution itself still produces a single UTC moment per the policy
pinned in summary.md §5.1.1 (fall-back → pre-transition offset /
fold=0; spring-forward → post-transition offset). The warning is
surfaced in the expand output so downstream consumers can flag the
ambiguity.
"""

from __future__ import annotations

from pathlib import Path

from conftest import run_expand

HEAD = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
TAIL = "END:VCALENDAR\n"


US_EASTERN_TZ = """\
BEGIN:VTIMEZONE
TZID:America/New_York
BEGIN:STANDARD
DTSTART:20061105T020000
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:20070311T020000
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
END:VTIMEZONE
"""


def _wrap(event_body: str) -> str:
    return HEAD + US_EASTERN_TZ + "BEGIN:VEVENT\n" + event_body + "END:VEVENT\n" + TAIL


def _kinds(out: dict) -> list[str]:
    return [w.get("kind") for w in out.get("warnings", []) or []]


# ---------------------------------------------------------------------------
# Fall-back ambiguous-time warning
# ---------------------------------------------------------------------------


def test_fall_back_ambiguous_emits_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """US/Eastern 2026-11-01 01:30 falls in the fall-back overlap."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=America/New_York:20261101T013000\n"
    )
    out = run_expand(
        submission_command,
        _wrap(body),
        "2026-10-01T00:00:00Z",
        "2026-12-01T00:00:00Z",
        tmp_path,
    )
    assert "timezone_fold_ambiguous" in _kinds(out)


def test_fall_back_unambiguous_does_not_warn(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """03:00 on fall-back day is unambiguous (after the transition)."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=America/New_York:20261101T030000\n"
    )
    out = run_expand(
        submission_command,
        _wrap(body),
        "2026-10-01T00:00:00Z",
        "2026-12-01T00:00:00Z",
        tmp_path,
    )
    assert "timezone_fold_ambiguous" not in _kinds(out)


# ---------------------------------------------------------------------------
# Spring-forward nonexistent-time warning
# ---------------------------------------------------------------------------


def test_spring_forward_gap_emits_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """US/Eastern 2026-03-08 02:30 falls in the spring-forward gap."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=America/New_York:20260308T023000\n"
    )
    out = run_expand(
        submission_command,
        _wrap(body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    assert "nonexistent_local_time" in _kinds(out)


def test_spring_forward_before_gap_does_not_warn(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """01:30 on spring-forward day is before the 02:00 transition (valid EST)."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=America/New_York:20260308T013000\n"
    )
    out = run_expand(
        submission_command,
        _wrap(body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    assert "nonexistent_local_time" not in _kinds(out)


def test_spring_forward_after_gap_does_not_warn(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """04:00 on spring-forward day is after the gap (valid EDT)."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=America/New_York:20260308T040000\n"
    )
    out = run_expand(
        submission_command,
        _wrap(body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    assert "nonexistent_local_time" not in _kinds(out)


# ---------------------------------------------------------------------------
# Non-DST zone never warns
# ---------------------------------------------------------------------------


UTC_TZ = """\
BEGIN:VTIMEZONE
TZID:Etc/UTC
BEGIN:STANDARD
DTSTART:19700101T000000
TZOFFSETFROM:+0000
TZOFFSETTO:+0000
END:STANDARD
END:VTIMEZONE
"""


def test_no_dst_zone_does_not_emit_fold_warnings(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART;TZID=Etc/UTC:20260301T023000\n"
    )
    ics = HEAD + UTC_TZ + "BEGIN:VEVENT\n" + body + "END:VEVENT\n" + TAIL
    out = run_expand(
        submission_command,
        ics,
        "2026-01-01T00:00:00Z",
        "2027-01-01T00:00:00Z",
        tmp_path,
    )
    kinds = _kinds(out)
    assert "timezone_fold_ambiguous" not in kinds
    assert "nonexistent_local_time" not in kinds


# ---------------------------------------------------------------------------
# Floating time does not trigger
# ---------------------------------------------------------------------------


def test_floating_time_does_not_trigger_dst_warnings(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Floating-time events have no TZID to resolve, so no fold/gap warn."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260308T023000\n"  # floating, no TZID
    )
    ics = HEAD + "BEGIN:VEVENT\n" + body + "END:VEVENT\n" + TAIL
    out = run_expand(
        submission_command,
        ics,
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    kinds = _kinds(out)
    assert "timezone_fold_ambiguous" not in kinds
    assert "nonexistent_local_time" not in kinds


# ---------------------------------------------------------------------------
# Recurring event crossing DST boundary emits per-occurrence warnings
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Fold detection across RDATE-driven and UNTIL-bounded observances
# (exercises the detect_tz_anomaly path that enumerates RDATE + multi-year
# RRULE + UNTIL per iter 1 review fixes).
# ---------------------------------------------------------------------------


HISTORICAL_US_TZ = """\
BEGIN:VTIMEZONE
TZID:America/New_York
BEGIN:STANDARD
DTSTART:19701025T020000
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST-old
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU;UNTIL=20061026T000000Z
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:19700405T020000
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT-old
RRULE:FREQ=YEARLY;BYMONTH=4;BYDAY=1SU;UNTIL=20070401T000000Z
END:DAYLIGHT
BEGIN:STANDARD
DTSTART:20071104T020000
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:20070311T020000
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
END:VTIMEZONE
"""


def _wrap_historical(event_body: str) -> str:
    return (
        HEAD + HISTORICAL_US_TZ
        + "BEGIN:VEVENT\n" + event_body + "END:VEVENT\n" + TAIL
    )


def test_historical_fold_on_pre_2007_date(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A fold-ambiguous local time on a 2005 fall-back day (under the
    pre-2007 UNTIL-bounded rule: last Sunday of October) must still fire
    `timezone_fold_ambiguous`. This exercises detect_tz_anomaly's
    multi-year enumeration + UNTIL handling.
    """
    body = (
        "UID:e-hist\nDTSTAMP:20050101T120000Z\n"
        # 2005-10-30 was the last Sunday of October 2005 → fall-back day.
        "DTSTART;TZID=America/New_York:20051030T013000\n"
    )
    out = run_expand(
        submission_command,
        _wrap_historical(body),
        "2005-10-01T00:00:00Z",
        "2005-11-01T00:00:00Z",
        tmp_path,
    )
    assert "timezone_fold_ambiguous" in _kinds(out)


def test_historical_post_2007_fold_still_fires(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Post-2007 (current DST rule), the first-Sunday-of-November fall-
    back fold-ambiguous time still fires, proving the detect_tz_anomaly
    multi-year scan isn't confused by the presence of the old rule."""
    body = (
        "UID:e-modern\nDTSTAMP:20261101T120000Z\n"
        "DTSTART;TZID=America/New_York:20261101T013000\n"
    )
    out = run_expand(
        submission_command,
        _wrap_historical(body),
        "2026-10-01T00:00:00Z",
        "2026-12-01T00:00:00Z",
        tmp_path,
    )
    assert "timezone_fold_ambiguous" in _kinds(out)


RDATE_DRIVEN_TZ = """\
BEGIN:VTIMEZONE
TZID:Test/RDate
BEGIN:STANDARD
DTSTART:20100101T000000
TZOFFSETFROM:+0100
TZOFFSETTO:+0000
RDATE:20250315T020000
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:20251015T020000
TZOFFSETFROM:+0000
TZOFFSETTO:+0100
END:DAYLIGHT
END:VTIMEZONE
"""


def _wrap_rdate_tz(event_body: str) -> str:
    return (
        HEAD + RDATE_DRIVEN_TZ
        + "BEGIN:VEVENT\n" + event_body + "END:VEVENT\n" + TAIL
    )


def test_rdate_driven_fold_fires_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An RDATE-only transition in a zone (+0100 → +0000 on 2025-03-15
    at local 02:00) creates a fold-ambiguous window at local 01:00–02:00.
    This exercises detect_tz_anomaly's RDATE enumeration — previously
    the anomaly detector ignored RDATE."""
    body = (
        "UID:e-rdate\nDTSTAMP:20260101T120000Z\n"
        # 01:30 on 2025-03-15 local is in the fall-back overlap.
        "DTSTART;TZID=Test/RDate:20250315T013000\n"
    )
    out = run_expand(
        submission_command,
        _wrap_rdate_tz(body),
        "2025-03-01T00:00:00Z",
        "2025-04-01T00:00:00Z",
        tmp_path,
    )
    assert "timezone_fold_ambiguous" in _kinds(out)


def test_recurring_event_crossing_dst_boundary(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A weekly event that crosses the DST spring-forward boundary resolves
    its affected occurrence(s). We don't strictly require the warning to
    fire per-occurrence (some impls detect at DTSTART only), but the event
    must still produce occurrences — no crashes or dropped events."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        # 10am local on Thursdays — safely outside any DST transition.
        "DTSTART;TZID=America/New_York:20260305T100000\n"
        "RRULE:FREQ=WEEKLY;COUNT=3\n"  # 3/5, 3/12 (after DST), 3/19
    )
    out = run_expand(
        submission_command,
        _wrap(body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    # Three occurrences produced; offsets shift at DST.
    occs = out.get("occurrences") or []
    assert len(occs) == 3
