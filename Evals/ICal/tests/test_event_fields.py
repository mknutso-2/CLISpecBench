"""Event-level fields promised by the schema but previously unmodeled.

Closes Codex v1.0 adversarial-review finding #2. The schema in
``technical-requirements-prompt.md`` listed ``priority``, ``transp``,
``url``, ``geo``, ``resources``, ``contact``, ``created``,
``last_modified``, ``attachments``, ``color``, ``images``,
``conferences`` on VEVENT but the reference impl wasn't parsing or
emitting most of them.

Each field gets a minimum of 1-3 focused tests here; none of these
should cascade on a generic event-shape regression because each
asserts via ``ev.get(field)``.

References:
  * RFC 5545 §3.8.1.1 ATTACH, §3.8.1.6 GEO, §3.8.1.9 PRIORITY,
    §3.8.1.10 RESOURCES, §3.8.2.7 TRANSP, §3.8.4.2 CONTACT,
    §3.8.4.6 URL, §3.8.7.1 CREATED, §3.8.7.3 LAST-MODIFIED.
  * RFC 7986 §5.9 COLOR, §5.10 IMAGE, §6.3 CONFERENCE (applicability
    extended to VEVENT / VTODO / VJOURNAL).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import find_event, run_parse, wrap_event


def _event_with(props: str, uid: str = "e1") -> str:
    body = f"UID:{uid}\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n{props}"
    return wrap_event(body)


# ---------------------------------------------------------------------------
# PRIORITY (§3.8.1.9)
# ---------------------------------------------------------------------------


def test_priority_integer(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """PRIORITY=5 surfaces as integer 5."""
    out = run_parse(submission_command, _event_with("PRIORITY:5\n"), tmp_path)
    ev = find_event(out, "e1")
    assert ev.get("priority") == 5


def test_priority_absent_is_null(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    out = run_parse(submission_command, _event_with(""), tmp_path)
    ev = find_event(out, "e1")
    assert ev.get("priority") in (None, 0) or ev["priority"] is None


# ---------------------------------------------------------------------------
# TRANSP (§3.8.2.7)
# ---------------------------------------------------------------------------


def test_transp_opaque(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    out = run_parse(submission_command, _event_with("TRANSP:OPAQUE\n"), tmp_path)
    ev = find_event(out, "e1")
    assert ev.get("transp") == "OPAQUE"


def test_transp_transparent(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    out = run_parse(
        submission_command, _event_with("TRANSP:TRANSPARENT\n"), tmp_path
    )
    ev = find_event(out, "e1")
    assert ev.get("transp") == "TRANSPARENT"


# ---------------------------------------------------------------------------
# URL (§3.8.4.6)
# ---------------------------------------------------------------------------


def test_url_preserved(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    out = run_parse(
        submission_command,
        _event_with("URL:https://example.com/e1\n"),
        tmp_path,
    )
    ev = find_event(out, "e1")
    assert ev.get("url") == "https://example.com/e1"


def test_url_absent_is_null(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    out = run_parse(submission_command, _event_with(""), tmp_path)
    ev = find_event(out, "e1")
    assert ev.get("url") is None


# ---------------------------------------------------------------------------
# GEO (§3.8.1.6)
# ---------------------------------------------------------------------------


def test_geo_two_floats(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """GEO:lat;lon parses into {"lat": float, "lon": float}."""
    out = run_parse(
        submission_command,
        _event_with("GEO:37.7749;-122.4194\n"),
        tmp_path,
    )
    ev = find_event(out, "e1")
    geo = ev.get("geo")
    assert isinstance(geo, dict)
    assert abs(cast(float, geo["lat"]) - 37.7749) < 0.01
    assert abs(cast(float, geo["lon"]) - (-122.4194)) < 0.01


def test_geo_absent_is_null(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    out = run_parse(submission_command, _event_with(""), tmp_path)
    assert find_event(out, "e1").get("geo") is None


def test_geo_malformed_emits_warning(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Malformed GEO value emits `malformed_value` warning; geo stays null."""
    out = run_parse(
        submission_command,
        _event_with("GEO:not-a-geo\n"),
        tmp_path,
    )
    ev = find_event(out, "e1")
    assert ev.get("geo") is None
    warnings = cast(list[dict[str, Any]], out.get("warnings") or [])
    kinds = [w.get("kind") for w in warnings]
    assert "malformed_value" in kinds


# ---------------------------------------------------------------------------
# RESOURCES (§3.8.1.10)
# ---------------------------------------------------------------------------


def test_resources_comma_separated_list(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    out = run_parse(
        submission_command,
        _event_with("RESOURCES:PROJECTOR,TABLE,MIC\n"),
        tmp_path,
    )
    ev = find_event(out, "e1")
    res = ev.get("resources")
    assert isinstance(res, list)
    assert "PROJECTOR" in cast(list[Any], res)
    assert "TABLE" in cast(list[Any], res)
    assert "MIC" in cast(list[Any], res)


def test_resources_absent_is_empty_list(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    out = run_parse(submission_command, _event_with(""), tmp_path)
    assert find_event(out, "e1").get("resources") == []


# ---------------------------------------------------------------------------
# CONTACT (§3.8.4.2)
# ---------------------------------------------------------------------------


def test_contact_text(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    out = run_parse(
        submission_command,
        _event_with("CONTACT:Jane Doe\\, tel:+1-555-1212\n"),
        tmp_path,
    )
    ev = find_event(out, "e1")
    c = ev.get("contact")
    assert c is not None
    assert "Jane Doe" in cast(str, c)


# ---------------------------------------------------------------------------
# CREATED (§3.8.7.1)
# ---------------------------------------------------------------------------


def test_created_utc_datetime(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    out = run_parse(
        submission_command,
        _event_with("CREATED:20251115T080000Z\n"),
        tmp_path,
    )
    ev = find_event(out, "e1")
    created = ev.get("created")
    assert isinstance(created, str) and created.endswith("Z")
    assert "2025-11-15" in created


# ---------------------------------------------------------------------------
# LAST-MODIFIED (§3.8.7.3)
# ---------------------------------------------------------------------------


def test_last_modified_utc_datetime(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    out = run_parse(
        submission_command,
        _event_with("LAST-MODIFIED:20260201T094500Z\n"),
        tmp_path,
    )
    ev = find_event(out, "e1")
    lm = ev.get("last_modified")
    assert isinstance(lm, str) and lm.endswith("Z")
    assert "2026-02-01" in lm


# ---------------------------------------------------------------------------
# ATTACH (§3.8.1.1)
# ---------------------------------------------------------------------------


def test_attach_uri_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """ATTACH with a URI value surfaces in attachments array."""
    out = run_parse(
        submission_command,
        _event_with("ATTACH:https://example.com/agenda.pdf\n"),
        tmp_path,
    )
    ev = find_event(out, "e1")
    atts = cast(list[dict[str, Any]], ev.get("attachments") or [])
    assert len(atts) == 1
    assert atts[0].get("value") == "https://example.com/agenda.pdf"


def test_attach_fmttype_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    out = run_parse(
        submission_command,
        _event_with(
            "ATTACH;FMTTYPE=application/pdf:https://example.com/a.pdf\n"
        ),
        tmp_path,
    )
    ev = find_event(out, "e1")
    atts = cast(list[dict[str, Any]], ev.get("attachments") or [])
    assert atts[0].get("fmttype") == "application/pdf"


def test_attach_inline_base64_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """Inline base64 attachment surfaces the encoding param."""
    out = run_parse(
        submission_command,
        _event_with(
            "ATTACH;ENCODING=BASE64;VALUE=BINARY:aGVsbG8=\n"
        ),
        tmp_path,
    )
    ev = find_event(out, "e1")
    atts = cast(list[dict[str, Any]], ev.get("attachments") or [])
    assert len(atts) == 1
    assert atts[0].get("value") == "aGVsbG8="
    assert atts[0].get("encoding") == "BASE64"


# ---------------------------------------------------------------------------
# RFC 7986 fields on VEVENT
# ---------------------------------------------------------------------------


def test_color_preserved_on_event(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 7986 §5.9 COLOR can appear on VEVENT."""
    out = run_parse(
        submission_command,
        _event_with("COLOR:cornflowerblue\n"),
        tmp_path,
    )
    ev = find_event(out, "e1")
    assert ev.get("color") == "cornflowerblue"


def test_image_on_event(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """RFC 7986 §5.10 IMAGE can appear on VEVENT (not just VCALENDAR)."""
    out = run_parse(
        submission_command,
        _event_with(
            "IMAGE;VALUE=URI;FMTTYPE=image/png;DISPLAY=BADGE:https://example.com/i.png\n"
        ),
        tmp_path,
    )
    ev = find_event(out, "e1")
    images = cast(list[dict[str, Any]], ev.get("images") or [])
    assert len(images) == 1
    assert images[0].get("fmttype") == "image/png"
    assert images[0].get("display") == "BADGE"


def test_conference_on_event(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RFC 7986 §6.3 CONFERENCE at event level."""
    out = run_parse(
        submission_command,
        _event_with(
            'CONFERENCE;FEATURE=VIDEO;LABEL="Zoom":https://zoom.us/j/123\n'
        ),
        tmp_path,
    )
    ev = find_event(out, "e1")
    confs = cast(list[dict[str, Any]], ev.get("conferences") or [])
    assert len(confs) == 1
    assert confs[0].get("feature") == "VIDEO"
    assert confs[0].get("label") == "Zoom"
