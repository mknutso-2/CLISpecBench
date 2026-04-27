"""RRULE parsing into structured form. Spec §4."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import find_event, run_parse, warnings_of, wrap_event


def _rrule(submission_command: tuple[str, ...], tmp_path: Path, rrule: str) -> dict[str, Any]:
    ics = wrap_event(f"UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\nRRULE:{rrule}\n")
    out = run_parse(submission_command, ics, tmp_path)
    return cast(dict[str, Any], find_event(out, "e1")["rrule"])


def test_rrule_freq(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    r = _rrule(submission_command, tmp_path, "FREQ=WEEKLY")
    assert r["freq"] == "WEEKLY"


def test_rrule_interval_default_1(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    r = _rrule(submission_command, tmp_path, "FREQ=DAILY")
    assert r["interval"] == 1


def test_rrule_interval_custom(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    r = _rrule(submission_command, tmp_path, "FREQ=DAILY;INTERVAL=3")
    assert r["interval"] == 3


def test_rrule_count(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    r = _rrule(submission_command, tmp_path, "FREQ=DAILY;COUNT=5")
    assert r["count"] == 5


def test_rrule_until(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    r = _rrule(submission_command, tmp_path, "FREQ=DAILY;UNTIL=20260401T000000Z")
    assert r["until"] == "2026-04-01T00:00:00Z"


def test_rrule_byday(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    r = _rrule(submission_command, tmp_path, "FREQ=WEEKLY;BYDAY=MO,WE,FR")
    weekdays = [e["weekday"] for e in r["byday"]]
    assert weekdays == ["MO", "WE", "FR"]


def test_rrule_byday_ordinal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    r = _rrule(submission_command, tmp_path, "FREQ=MONTHLY;BYDAY=2TU")
    assert r["byday"][0]["weekday"] == "TU"
    assert r["byday"][0]["ordinal"] == 2


def test_rrule_byday_negative_ordinal(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    r = _rrule(submission_command, tmp_path, "FREQ=MONTHLY;BYDAY=-1FR")
    assert r["byday"][0]["weekday"] == "FR"
    assert r["byday"][0]["ordinal"] == -1


def test_rrule_bymonthday(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    r = _rrule(submission_command, tmp_path, "FREQ=MONTHLY;BYMONTHDAY=1,15")
    assert r["bymonthday"] == [1, 15]


def test_rrule_bymonth(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    r = _rrule(submission_command, tmp_path, "FREQ=YEARLY;BYMONTH=3,6,9,12")
    assert r["bymonth"] == [3, 6, 9, 12]


def test_rrule_bysetpos(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    r = _rrule(submission_command, tmp_path, "FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYSETPOS=-1")
    assert r["bysetpos"] == [-1]


def test_rrule_wkst(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    r = _rrule(submission_command, tmp_path, "FREQ=WEEKLY;BYDAY=SU,MO;WKST=SU")
    assert r["wkst"] == "SU"


def test_hourly_freq_supported_v02(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # v0.2: HOURLY / MINUTELY / SECONDLY are fully supported (no warning).
    ics = wrap_event(
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\nRRULE:FREQ=HOURLY;COUNT=3\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    kinds = [w.get("kind") for w in warnings_of(out)]
    assert "unsupported_freq" not in kinds


def test_byhour_supported_v02(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    # v0.2: BYHOUR / BYMINUTE / BYSECOND / BYYEARDAY / BYWEEKNO parse without warning.
    ics = wrap_event(
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "RRULE:FREQ=DAILY;BYHOUR=9,10,11\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    kinds = [w.get("kind") for w in warnings_of(out)]
    assert "unsupported_rrule_part" not in kinds


def test_rrule_count_and_until_mutually_exclusive(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 5545 §3.3.10: UNTIL and COUNT MUST NOT occur in the same
    'recur' part. When an RRULE carries both, the parser emits a
    `malformed_value` warning. We parse both keys so the raw RRULE
    round-trips in the JSON (downstream tooling can inspect the
    invalid state); the warning signals the violation."""
    ics = wrap_event(
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\n"
        "RRULE:FREQ=DAILY;COUNT=5;UNTIL=20260401T000000Z\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    kinds = [w.get("kind") for w in warnings_of(out)]
    assert "malformed_value" in kinds


def test_rrule_count_without_until_does_not_warn(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Complement: COUNT alone (or UNTIL alone) is legal. Guards
    against an over-eager impl that warns on any COUNT presence."""
    ics = wrap_event(
        "UID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\nRRULE:FREQ=DAILY;COUNT=5\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    kinds = [w.get("kind") for w in warnings_of(out)]
    assert "malformed_value" not in kinds
