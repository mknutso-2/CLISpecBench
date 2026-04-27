"""RDATE;VALUE=PERIOD per RFC 5545 §3.8.5.2 and §3.3.9.

RDATE values may be plain DATE-TIME / DATE strings, or PERIOD values.
A PERIOD is either:
  * `period-explicit`: `<start-DT> "/" <end-DT>` (start MUST be < end)
  * `period-start`:    `<start-DT> "/" <positive-duration>`

In the parse-output schema, `rdate` is a list of entries, each either a
plain ISO-8601 string OR a period object of the form:

    {"start": "<ISO>", "end": "<ISO>"} | {"start": "<ISO>", "duration": "<ISO-8601 dur>"}

During `expand`, period-typed RDATEs add an occurrence whose `dtstart`
is the period's start. Per §3.8.5.3: "The duration of a specific
recurrence may be modified ... simply by using an RDATE property of
PERIOD value type." Implementations therefore reflect the period's
endpoint on the occurrence's `dtend` (or a derived field).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import find_event, occurrences_of, run_expand, run_parse, starts_for, wrap_event


def _rdate_of(ev: dict[str, Any]) -> list[Any]:
    r = ev.get("rdate")
    assert isinstance(r, list), f"event has no rdate list; got keys {list(ev)}"
    return cast(list[Any], r)


def test_rdate_period_explicit_parsed(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.3.9 period-explicit: start/end DATE-TIMEs joined by SOLIDUS.
    Parsed into `{"start": ..., "end": ...}` object in the rdate list."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "RDATE;VALUE=PERIOD:20260310T090000Z/20260310T110000Z\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    rdates = _rdate_of(find_event(out, "e1"))
    assert len(rdates) == 1
    entry_raw = rdates[0]
    assert isinstance(entry_raw, dict), (
        f"period RDATE must parse to an object, got {type(entry_raw).__name__}"
    )
    entry = cast(dict[str, Any], entry_raw)
    assert entry.get("start") == "2026-03-10T09:00:00Z"
    assert entry.get("end") == "2026-03-10T11:00:00Z"


def test_rdate_period_start_duration_parsed(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.3.9 period-start: start DATE-TIME and positive duration."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "RDATE;VALUE=PERIOD:20260310T090000Z/PT2H30M\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    entry_raw = _rdate_of(find_event(out, "e1"))[0]
    assert isinstance(entry_raw, dict)
    entry = cast(dict[str, Any], entry_raw)
    assert entry.get("start") == "2026-03-10T09:00:00Z"
    assert entry.get("duration") == "PT2H30M"
    # Duration-form period must NOT expose an `end` key (or it is null/absent).
    assert entry.get("end") in (None, "")


def test_rdate_period_multiple_comma_separated(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.8.5.2 RDATE accepts a comma-separated list of period values."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "RDATE;VALUE=PERIOD:"
        "20260310T090000Z/20260310T110000Z,"
        "20260311T090000Z/PT1H\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    rdates = _rdate_of(find_event(out, "e1"))
    assert len(rdates) == 2
    # First entry is explicit period; second is start+duration.
    first, second = rdates
    assert first.get("start") == "2026-03-10T09:00:00Z"
    assert first.get("end") == "2026-03-10T11:00:00Z"
    assert second.get("start") == "2026-03-11T09:00:00Z"
    assert second.get("duration") == "PT1H"


def test_rdate_mixed_value_types_not_allowed_but_period_only_ok(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.8.5.2: a single RDATE property uses one VALUE type. Plain DATE-TIME
    and PERIOD in separate properties must coexist on the same event."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "RDATE:20260315T090000Z\n"
        "RDATE;VALUE=PERIOD:20260320T090000Z/PT1H\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    rdates = _rdate_of(find_event(out, "e1"))
    assert len(rdates) == 2
    # First must be a plain string; second must be an object.
    types = {type(r).__name__ for r in rdates}
    assert "str" in types
    assert "dict" in types


def test_rdate_period_adds_occurrence(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.8.5.2: a PERIOD-valued RDATE adds an occurrence at the period start."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "RDATE;VALUE=PERIOD:20260310T090000Z/PT90M\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    starts = starts_for(occurrences_of(out), "e1")
    assert "2026-03-01T10:00:00Z" in starts
    assert "2026-03-10T09:00:00Z" in starts


def test_rdate_period_explicit_sets_occurrence_end(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.8.5.3 & §3.8.5.2: a PERIOD-valued RDATE overrides the default duration;
    the generated occurrence's dtend reflects the period's end."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nDTEND:20260301T103000Z\n"
        "RDATE;VALUE=PERIOD:20260310T090000Z/20260310T113000Z\n"
    )
    out = run_expand(
        submission_command,
        wrap_event(body),
        "2026-03-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        tmp_path,
    )
    # Find the occurrence at the RDATE time.
    occ_at_rdate = [o for o in occurrences_of(out) if o.get("dtstart") == "2026-03-10T09:00:00Z"]
    assert len(occ_at_rdate) == 1
    # Period was 09:00–11:30 UTC (2h30m), different from the default 30m duration.
    assert occ_at_rdate[0].get("dtend") == "2026-03-10T11:30:00Z"


def test_rdate_period_invalid_end_before_start_warns(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.3.9: "The start MUST be before the end." A reversed period is malformed;
    the parser emits `malformed_value` and either drops the entry or preserves
    it untouched, but MUST NOT crash."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        # end < start
        "RDATE;VALUE=PERIOD:20260310T110000Z/20260310T090000Z\n"
        "SUMMARY:ok\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    ev = find_event(out, "e1")
    # Event itself must remain intact.
    assert ev.get("summary") == "ok"
    kinds = [w.get("kind") for w in out.get("warnings", [])]
    assert "malformed_value" in kinds


def test_rdate_period_raw_property_retained(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.8.5.2 RDATE;VALUE=PERIOD: raw_properties must preserve the VALUE=PERIOD param."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "RDATE;VALUE=PERIOD:20260310T090000Z/PT1H\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    raw = find_event(out, "e1").get("raw_properties")
    assert isinstance(raw, list)
    rdate_raws: list[dict[str, Any]] = []
    for p in cast(list[Any], raw):
        if not isinstance(p, dict):
            continue
        p_dict = cast(dict[str, Any], p)
        name = p_dict.get("name")
        if isinstance(name, str) and name.upper() == "RDATE":
            rdate_raws.append(p_dict)
    assert len(rdate_raws) >= 1
    params = cast(dict[str, Any], rdate_raws[0].get("params") or {})
    # Params are typically upper-cased by parsers.
    val_param = {k.upper(): v for k, v in params.items()}.get("VALUE")
    assert val_param == "PERIOD"
