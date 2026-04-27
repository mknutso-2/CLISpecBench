"""RFC 7986 calendar-level properties.

RFC 7986 §4 extends VCALENDAR with new top-level properties that describe
the calendar as a whole (rather than any single component):

    NAME              (§5.1)  TEXT          calendar display name
    DESCRIPTION       (§5.2)  TEXT          long-form description
    REFRESH-INTERVAL  (§5.7)  DURATION      minimum polling interval
    SOURCE            (§5.8)  URI           where to refresh data from
    COLOR             (§5.9)  TEXT (CSS3)   display color
    URL               (§5.5)  URI           alternate rendition URL
    CATEGORIES        (§5.6)  TEXT list     calendar-level categories
    IMAGE             (§5.10) URI|BINARY    calendar image (can repeat)
    CONFERENCE        (§5.11) URI           conferencing URI (can repeat)

Per technical-requirements-prompt.md, all of these live on the top-level
`calendar` object in the parse output:

    "calendar": {
        "prodid": ..., "version": ..., "calscale": ..., "method": ...,
        "name": "string|null", "description": "string|null",
        "refresh_interval": "ISO-8601 duration|null",
        "source": "URI|null", "color": "string|null", "url": "URI|null",
        "categories": ["string", ...],
        "images": [{"value": ..., "fmttype": ..., "encoding": ...,
                     "display": ...}, ...],
        "conferences": [{"value": ..., "feature": ..., "label": ...}, ...]
    }

Tests here assert: presence of these keys on the calendar object, proper
typing, and correct decoding of individual property values.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import run_parse


def _cal(out: dict[str, Any]) -> dict[str, Any]:
    """Return the calendar object or an empty dict — so schema bugs surface as
    key-missing rather than cascading AttributeErrors."""
    c = out.get("calendar")
    return cast(dict[str, Any], c) if isinstance(c, dict) else {}


def _list_field(d: dict[str, Any], key: str) -> list[Any]:
    return cast(list[Any], d.get(key) or [])


def _dict_list_field(d: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], d.get(key) or [])


def _wrap_calprops(calprops: str, include_event: bool = True) -> str:
    """Build a VCALENDAR with the given calendar-level properties."""
    event = (
        "BEGIN:VEVENT\nUID:e1\nDTSTAMP:20260420T120000Z\nDTSTART:20260305T100000Z\nEND:VEVENT\n"
        if include_event
        else ""
    )
    return "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n" + calprops + event + "END:VCALENDAR\n"


# ---------------------------------------------------------------------------
# Baseline: all new keys are present (as null/empty) even when absent from input
# ---------------------------------------------------------------------------


def test_calendar_has_rfc7986_keys_even_when_absent(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """When the input VCALENDAR has none of the RFC 7986 properties, the
    calendar object MUST still expose the keys with their null / empty-list
    defaults. This lets downstream consumers index without KeyError."""
    out = run_parse(submission_command, _wrap_calprops(""), tmp_path)
    cal = _cal(out)
    # Scalar optional fields default to None/null.
    assert "name" in cal
    assert "description" in cal
    assert "refresh_interval" in cal
    assert "source" in cal
    assert "color" in cal
    assert "url" in cal
    # List fields default to [].
    assert isinstance(cal.get("categories"), list)
    assert isinstance(cal.get("images"), list)
    assert isinstance(cal.get("conferences"), list)


# ---------------------------------------------------------------------------
# NAME (RFC 7986 §5.1)
# ---------------------------------------------------------------------------


def test_calendar_name_parsed(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """RFC 7986 §5.1: NAME carries a TEXT value that names the calendar."""
    out = run_parse(
        submission_command,
        _wrap_calprops("NAME:Company Vacation Days\n"),
        tmp_path,
    )
    assert _cal(out).get("name") == "Company Vacation Days"


def test_calendar_name_with_text_escapes(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """NAME is a TEXT-typed property (RFC 7986 §5.1), so RFC 5545 §3.3.11 text
    escapes apply: `\\,` → `,`, `\\n` → newline, `\\\\` → `\\`."""
    out = run_parse(
        submission_command,
        _wrap_calprops("NAME:Team\\, Ops\\nSchedule\n"),
        tmp_path,
    )
    assert _cal(out).get("name") == "Team, Ops\nSchedule"


# ---------------------------------------------------------------------------
# DESCRIPTION (RFC 7986 §5.2)
# ---------------------------------------------------------------------------


def test_calendar_description_parsed(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """RFC 7986 §5.2: DESCRIPTION at the VCALENDAR level is a lengthy textual
    description of the calendar (not of any single event)."""
    out = run_parse(
        submission_command,
        _wrap_calprops("DESCRIPTION:All company-wide holidays and vacations.\n"),
        tmp_path,
    )
    assert _cal(out).get("description") == "All company-wide holidays and vacations."


# ---------------------------------------------------------------------------
# REFRESH-INTERVAL (RFC 7986 §5.7)
# ---------------------------------------------------------------------------


def test_calendar_refresh_interval_parsed(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 7986 §5.7 example: `REFRESH-INTERVAL;VALUE=DURATION:P1W` — a one-week
    polling interval. Schema requires ISO-8601 duration string representation."""
    out = run_parse(
        submission_command,
        _wrap_calprops("REFRESH-INTERVAL;VALUE=DURATION:P1W\n"),
        tmp_path,
    )
    assert _cal(out).get("refresh_interval") == "P1W"


def test_calendar_refresh_interval_complex_duration(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A compound duration `P1DT12H` (1 day + 12 hours) must round-trip to the
    ISO-8601 form per the harness's duration normalization rule."""
    out = run_parse(
        submission_command,
        _wrap_calprops("REFRESH-INTERVAL;VALUE=DURATION:P1DT12H\n"),
        tmp_path,
    )
    # Accept either P1DT12H (canonical) or equivalent normalized form.
    val = _cal(out).get("refresh_interval")
    assert val == "P1DT12H"


# ---------------------------------------------------------------------------
# SOURCE (RFC 7986 §5.8)
# ---------------------------------------------------------------------------


def test_calendar_source_parsed(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """RFC 7986 §5.8 example: `SOURCE;VALUE=URI:https://example.com/holidays.ics`.
    The URI is preserved verbatim."""
    out = run_parse(
        submission_command,
        _wrap_calprops("SOURCE;VALUE=URI:https://example.com/holidays.ics\n"),
        tmp_path,
    )
    assert _cal(out).get("source") == "https://example.com/holidays.ics"


# ---------------------------------------------------------------------------
# COLOR (RFC 7986 §5.9)
# ---------------------------------------------------------------------------


def test_calendar_color_parsed(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """RFC 7986 §5.9 example: `COLOR:turquoise` — a CSS3 color name."""
    out = run_parse(
        submission_command,
        _wrap_calprops("COLOR:turquoise\n"),
        tmp_path,
    )
    assert _cal(out).get("color") == "turquoise"


# ---------------------------------------------------------------------------
# URL (RFC 7986 §5.5)
# ---------------------------------------------------------------------------


def test_calendar_url_parsed(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """RFC 7986 §5.5 allows URL at the VCALENDAR level to point at an
    alternative rendition of the calendar."""
    out = run_parse(
        submission_command,
        _wrap_calprops("URL:https://example.com/calendar.html\n"),
        tmp_path,
    )
    assert _cal(out).get("url") == "https://example.com/calendar.html"


# ---------------------------------------------------------------------------
# CATEGORIES (RFC 7986 §5.6) — comma-separated, can repeat for union
# ---------------------------------------------------------------------------


def test_calendar_categories_parsed(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """RFC 7986 §5.6 redefines CATEGORIES at calendar level: `CATEGORIES:work,
    personal` splits on commas into a list."""
    out = run_parse(
        submission_command,
        _wrap_calprops("CATEGORIES:work,personal,project-x\n"),
        tmp_path,
    )
    cats = _list_field(_cal(out), "categories")
    assert cats == ["work", "personal", "project-x"]


def test_calendar_categories_multiple_properties_union(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 7986 §5.6 Description: "When multiple [CATEGORIES] properties are
    present, the set of categories that apply to the iCalendar object are the
    union of all the categories listed in each property value." So two
    CATEGORIES lines should produce a combined list (order-preserved, not
    deduplicated)."""
    out = run_parse(
        submission_command,
        _wrap_calprops("CATEGORIES:work,urgent\nCATEGORIES:holiday\n"),
        tmp_path,
    )
    cats = _list_field(_cal(out), "categories")
    assert "work" in cats
    assert "urgent" in cats
    assert "holiday" in cats


# ---------------------------------------------------------------------------
# IMAGE (RFC 7986 §5.10) — URI or BINARY, can repeat
# ---------------------------------------------------------------------------


def test_calendar_image_uri_parsed(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """RFC 7986 §5.10 example: `IMAGE;VALUE=URI;DISPLAY=BADGE;FMTTYPE=image/png:
    http://example.com/images/party.png`. All three parameters (VALUE, DISPLAY,
    FMTTYPE) plus the URI value MUST be surfaced on the images[] entry."""
    out = run_parse(
        submission_command,
        _wrap_calprops(
            "IMAGE;VALUE=URI;DISPLAY=BADGE;FMTTYPE=image/png:http://example.com/images/party.png\n"
        ),
        tmp_path,
    )
    images = _dict_list_field(_cal(out), "images")
    assert len(images) == 1
    img = images[0]
    assert img.get("value") == "http://example.com/images/party.png"
    assert img.get("fmttype") == "image/png"
    assert img.get("display") == "BADGE"


def test_calendar_image_multiple_entries(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 7986 §5.10 allows IMAGE to be specified multiple times on the
    VCALENDAR (for alternate resolutions / media types). Two IMAGE lines =>
    two entries in images[]."""
    out = run_parse(
        submission_command,
        _wrap_calprops(
            "IMAGE;VALUE=URI;FMTTYPE=image/png:http://example.com/a.png\n"
            "IMAGE;VALUE=URI;FMTTYPE=image/jpeg:http://example.com/b.jpg\n"
        ),
        tmp_path,
    )
    images = _dict_list_field(_cal(out), "images")
    assert len(images) == 2
    fmttypes = {img.get("fmttype") for img in images}
    assert fmttypes == {"image/png", "image/jpeg"}


def test_calendar_image_display_values_comma_list(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 7986 §6.1 allows the DISPLAY parameter to carry multiple values
    (comma-separated): `DISPLAY=BADGE,THUMBNAIL`. The entire DISPLAY string
    should be surfaced; we accept either the raw joined string or a semantic
    split (depending on harness preference)."""
    out = run_parse(
        submission_command,
        _wrap_calprops(
            "IMAGE;VALUE=URI;DISPLAY=BADGE,THUMBNAIL;FMTTYPE=image/png:"
            "https://example.com/weather-cloudy.png\n"
        ),
        tmp_path,
    )
    images = _dict_list_field(_cal(out), "images")
    assert len(images) == 1
    display = cast(str, images[0].get("display") or "")
    assert "BADGE" in display and "THUMBNAIL" in display


# ---------------------------------------------------------------------------
# CONFERENCE (RFC 7986 §5.11) — can repeat, has FEATURE + LABEL params
# ---------------------------------------------------------------------------


def test_calendar_conference_parsed(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """RFC 7986 §5.11 example: `CONFERENCE;VALUE=URI;FEATURE=PHONE,MODERATOR;
    LABEL=Moderator dial-in:tel:+1-412-555-0123,,,654321`. The URI value must
    be preserved verbatim (including embedded commas — the colon separator is
    what matters)."""
    out = run_parse(
        submission_command,
        _wrap_calprops(
            "CONFERENCE;VALUE=URI;FEATURE=VIDEO;LABEL=Main video room:"
            "https://video.example.com/room/123\n"
        ),
        tmp_path,
    )
    confs = _dict_list_field(_cal(out), "conferences")
    assert len(confs) == 1
    conf = confs[0]
    assert conf.get("value") == "https://video.example.com/room/123"
    # FEATURE may be surfaced as a string ("VIDEO") or list (["VIDEO"]).
    feature = conf.get("feature")
    assert feature == "VIDEO" or (
        isinstance(feature, list) and cast(list[Any], feature) == ["VIDEO"]
    )
    assert conf.get("label") == "Main video room"


def test_calendar_conference_multiple_entries(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A VCALENDAR can carry multiple CONFERENCE properties (one per
    modality). Two CONFERENCE lines => two entries in conferences[]."""
    out = run_parse(
        submission_command,
        _wrap_calprops(
            "CONFERENCE;VALUE=URI;FEATURE=PHONE;LABEL=Dial-in:"
            "tel:+1-412-555-0123\n"
            "CONFERENCE;VALUE=URI;FEATURE=CHAT;LABEL=Chat room:"
            "xmpp:chat@conference.example.com\n"
        ),
        tmp_path,
    )
    confs = _dict_list_field(_cal(out), "conferences")
    assert len(confs) == 2
    values = {c.get("value") for c in confs}
    assert "tel:+1-412-555-0123" in values
    assert "xmpp:chat@conference.example.com" in values


# ---------------------------------------------------------------------------
# All properties together
# ---------------------------------------------------------------------------


def test_calendar_all_rfc7986_properties_together(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """A VCALENDAR populated with every RFC 7986 calendar-level property must
    parse correctly: no one property should shadow another."""
    calprops = (
        "NAME:My Cal\n"
        "DESCRIPTION:The big one\n"
        "REFRESH-INTERVAL;VALUE=DURATION:P1D\n"
        "SOURCE;VALUE=URI:https://example.com/src.ics\n"
        "COLOR:blue\n"
        "URL:https://example.com/view\n"
        "CATEGORIES:work\n"
        "IMAGE;VALUE=URI;FMTTYPE=image/png:https://example.com/i.png\n"
        "CONFERENCE;VALUE=URI;FEATURE=VIDEO;LABEL=Room:"
        "https://example.com/room\n"
    )
    out = run_parse(submission_command, _wrap_calprops(calprops), tmp_path)
    cal = _cal(out)
    assert cal.get("name") == "My Cal"
    assert cal.get("description") == "The big one"
    assert cal.get("refresh_interval") == "P1D"
    assert cal.get("source") == "https://example.com/src.ics"
    assert cal.get("color") == "blue"
    assert cal.get("url") == "https://example.com/view"
    assert _list_field(cal, "categories") == ["work"]
    images = _dict_list_field(cal, "images")
    assert len(images) == 1
    assert images[0].get("value") == "https://example.com/i.png"
    confs = _dict_list_field(cal, "conferences")
    assert len(confs) == 1
    assert confs[0].get("value") == "https://example.com/room"


# ---------------------------------------------------------------------------
# Empty calendar (no events, just RFC 7986 properties)
# ---------------------------------------------------------------------------


def test_calendar_properties_without_any_component(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 7986 enables "calendar-only" ICS files (e.g. a subscription stub
    with SOURCE + REFRESH-INTERVAL and no events). This must parse without
    errors: events / todos / journals / freebusy arrays are empty."""
    out = run_parse(
        submission_command,
        _wrap_calprops(
            "NAME:Subscription stub\n"
            "SOURCE;VALUE=URI:https://example.com/real.ics\n"
            "REFRESH-INTERVAL;VALUE=DURATION:PT6H\n",
            include_event=False,
        ),
        tmp_path,
    )
    cal = _cal(out)
    assert cal.get("name") == "Subscription stub"
    assert cal.get("source") == "https://example.com/real.ics"
    assert cal.get("refresh_interval") == "PT6H"
    assert _list_field(out, "events") == []
    assert _list_field(out, "todos") == []
    assert _list_field(out, "journals") == []
