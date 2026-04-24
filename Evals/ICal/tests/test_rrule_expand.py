"""RRULE expansion tests. The core adversarial surface. Spec §4."""

from __future__ import annotations

from pathlib import Path

from conftest import run_expand, starts_for, wrap_event


def _expand(
    submission_command: tuple[str, ...],
    tmp_path: Path,
    dtstart: str,
    rrule: str,
    from_: str,
    to_: str,
) -> list[str]:
    body = f"UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:{dtstart}\nRRULE:{rrule}\n"
    out = run_expand(submission_command, wrap_event(body), from_, to_, tmp_path)
    return starts_for(out["occurrences"], "e1")


# --- DAILY ---


def test_daily_simple(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    starts = _expand(
        submission_command,
        tmp_path,
        "20260305T100000Z",
        "FREQ=DAILY;COUNT=3",
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
    )
    assert starts == [
        "2026-03-05T10:00:00Z",
        "2026-03-06T10:00:00Z",
        "2026-03-07T10:00:00Z",
    ]


def test_daily_interval(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    starts = _expand(
        submission_command,
        tmp_path,
        "20260305T100000Z",
        "FREQ=DAILY;INTERVAL=2;COUNT=4",
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
    )
    assert starts == [
        "2026-03-05T10:00:00Z",
        "2026-03-07T10:00:00Z",
        "2026-03-09T10:00:00Z",
        "2026-03-11T10:00:00Z",
    ]


def test_daily_until(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    starts = _expand(
        submission_command,
        tmp_path,
        "20260305T100000Z",
        "FREQ=DAILY;UNTIL=20260308T100000Z",
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
    )
    assert starts == [
        "2026-03-05T10:00:00Z",
        "2026-03-06T10:00:00Z",
        "2026-03-07T10:00:00Z",
        "2026-03-08T10:00:00Z",
    ]


# --- WEEKLY ---


def test_weekly_byday_multiple(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # DTSTART is Thu 2026-03-05. BYDAY=MO,WE,FR. Should emit Fri 3/6 first,
    # then Mon 3/9, Wed 3/11, Fri 3/13, ...
    starts = _expand(
        submission_command,
        tmp_path,
        "20260305T100000Z",
        "FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=6",
        "2026-03-01T00:00:00Z",
        "2026-05-01T00:00:00Z",
    )
    assert starts == [
        "2026-03-06T10:00:00Z",
        "2026-03-09T10:00:00Z",
        "2026-03-11T10:00:00Z",
        "2026-03-13T10:00:00Z",
        "2026-03-16T10:00:00Z",
        "2026-03-18T10:00:00Z",
    ]


def test_weekly_interval_2(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # Every other week, starting Thu 2026-03-05, BYDAY=TH.
    starts = _expand(
        submission_command,
        tmp_path,
        "20260305T100000Z",
        "FREQ=WEEKLY;INTERVAL=2;BYDAY=TH;COUNT=3",
        "2026-03-01T00:00:00Z",
        "2026-05-01T00:00:00Z",
    )
    assert starts == [
        "2026-03-05T10:00:00Z",
        "2026-03-19T10:00:00Z",
        "2026-04-02T10:00:00Z",
    ]


# --- MONTHLY ---


def test_monthly_bymonthday(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    starts = _expand(
        submission_command,
        tmp_path,
        "20260115T100000Z",
        "FREQ=MONTHLY;BYMONTHDAY=15;COUNT=3",
        "2026-01-01T00:00:00Z",
        "2026-06-01T00:00:00Z",
    )
    assert starts == [
        "2026-01-15T10:00:00Z",
        "2026-02-15T10:00:00Z",
        "2026-03-15T10:00:00Z",
    ]


def test_monthly_byday_ordinal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # Second Tuesday of the month, starting with the event on 2026-03-10.
    starts = _expand(
        submission_command,
        tmp_path,
        "20260310T140000Z",
        "FREQ=MONTHLY;BYDAY=2TU;COUNT=3",
        "2026-01-01T00:00:00Z",
        "2026-06-01T00:00:00Z",
    )
    assert starts == [
        "2026-03-10T14:00:00Z",
        "2026-04-14T14:00:00Z",
        "2026-05-12T14:00:00Z",
    ]


def test_monthly_byday_negative_ordinal(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # Last Friday of the month.
    starts = _expand(
        submission_command,
        tmp_path,
        "20260327T100000Z",
        "FREQ=MONTHLY;BYDAY=-1FR;COUNT=3",
        "2026-03-01T00:00:00Z",
        "2026-06-30T00:00:00Z",
    )
    assert starts == [
        "2026-03-27T10:00:00Z",
        "2026-04-24T10:00:00Z",
        "2026-05-29T10:00:00Z",
    ]


def test_monthly_bymonthday_invalid_dates_dropped(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # BYMONTHDAY=31 skips months with fewer than 31 days.
    # Starting 2026-01-31, months with 31 days: Jan, Mar, May, Jul, Aug, Oct, Dec.
    starts = _expand(
        submission_command,
        tmp_path,
        "20260131T100000Z",
        "FREQ=MONTHLY;BYMONTHDAY=31;COUNT=4",
        "2026-01-01T00:00:00Z",
        "2026-12-31T23:59:59Z",
    )
    assert starts == [
        "2026-01-31T10:00:00Z",
        "2026-03-31T10:00:00Z",
        "2026-05-31T10:00:00Z",
        "2026-07-31T10:00:00Z",
    ]


def test_monthly_bysetpos_last(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # Last weekday of the month: BYDAY=MO,TU,WE,TH,FR + BYSETPOS=-1.
    # March 2026 ends on Tue 3/31. April on Thu 4/30. May on Fri 5/29.
    starts = _expand(
        submission_command,
        tmp_path,
        "20260331T100000Z",
        "FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYSETPOS=-1;COUNT=3",
        "2026-03-01T00:00:00Z",
        "2026-06-30T00:00:00Z",
    )
    assert starts == [
        "2026-03-31T10:00:00Z",
        "2026-04-30T10:00:00Z",
        "2026-05-29T10:00:00Z",
    ]


def test_monthly_bymonthday_plus_byday_filter(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    # Friday the 13th: BYMONTHDAY=13 expanded then filtered by BYDAY=FR.
    # In 2026, Friday 13ths fall in: Feb, March, November.
    starts = _expand(
        submission_command,
        tmp_path,
        "20260213T100000Z",
        "FREQ=MONTHLY;BYMONTHDAY=13;BYDAY=FR;COUNT=3",
        "2026-01-01T00:00:00Z",
        "2027-01-01T00:00:00Z",
    )
    assert starts == [
        "2026-02-13T10:00:00Z",
        "2026-03-13T10:00:00Z",
        "2026-11-13T10:00:00Z",
    ]


# --- YEARLY ---


def test_yearly_simple(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    starts = _expand(
        submission_command,
        tmp_path,
        "20260301T100000Z",
        "FREQ=YEARLY;COUNT=3",
        "2026-01-01T00:00:00Z",
        "2030-01-01T00:00:00Z",
    )
    assert starts == [
        "2026-03-01T10:00:00Z",
        "2027-03-01T10:00:00Z",
        "2028-03-01T10:00:00Z",
    ]


def test_yearly_bymonth(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    starts = _expand(
        submission_command,
        tmp_path,
        "20260305T100000Z",
        "FREQ=YEARLY;BYMONTH=3,9;COUNT=4",
        "2026-01-01T00:00:00Z",
        "2028-01-01T00:00:00Z",
    )
    assert starts == [
        "2026-03-05T10:00:00Z",
        "2026-09-05T10:00:00Z",
        "2027-03-05T10:00:00Z",
        "2027-09-05T10:00:00Z",
    ]


# --- EXDATE / RDATE ---


def test_exdate_removes_occurrence(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = (
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "RRULE:FREQ=DAILY;COUNT=5\n"
        "EXDATE:20260307T100000Z\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    assert "2026-03-07T10:00:00Z" not in starts
    assert len(starts) == 4


def test_rdate_adds_occurrence(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\nRDATE:20260310T150000Z\n"
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(out["occurrences"], "e1")
    assert "2026-03-05T10:00:00Z" in starts
    assert "2026-03-10T15:00:00Z" in starts


# --- Window / sort ---


def test_occurrences_sorted_ascending(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # Two events both recurring weekly; output must be merge-sorted.
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test//EN\n"
        "BEGIN:VEVENT\nUID:late\nDTSTAMP:20260420T120000Z\nDTSTART:20260306T140000Z\n"
        "RRULE:FREQ=WEEKLY;BYDAY=FR;COUNT=2\nEND:VEVENT\n"
        "BEGIN:VEVENT\nUID:early\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "RRULE:FREQ=WEEKLY;BYDAY=TH;COUNT=2\nEND:VEVENT\n"
        "END:VCALENDAR\n"
    )
    out = run_expand(
        submission_command, ics, "2026-03-01T00:00:00Z", "2026-04-01T00:00:00Z", tmp_path
    )
    occs = out["occurrences"]
    for i in range(1, len(occs)):
        assert occs[i - 1]["dtstart"] <= occs[i]["dtstart"]


def test_window_excludes_outside(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    starts = _expand(
        submission_command,
        tmp_path,
        "20260305T100000Z",
        "FREQ=DAILY;COUNT=10",
        "2026-03-07T00:00:00Z",
        "2026-03-09T00:00:00Z",
    )
    # Window is [3/7, 3/9): should include 3/7, 3/8; exclude 3/5, 3/6, 3/9+.
    assert starts == ["2026-03-07T10:00:00Z", "2026-03-08T10:00:00Z"]


def test_non_recurring_event_in_window(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    body = "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260310T140000Z\nSUMMARY:single\n"
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    assert len(out["occurrences"]) == 1
    assert out["occurrences"][0]["dtstart"] == "2026-03-10T14:00:00Z"


def test_non_recurring_event_outside_window(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    body = "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260610T140000Z\nSUMMARY:single\n"
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    assert out["occurrences"] == []
