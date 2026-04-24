"""RFC 9253 — Support for iCalendar Relationships (August 2022).

Extends RFC 5545's RELATED-TO grammar for richer inter-component
relationships. This file asserts that the parser surfaces the new
vocabulary in `raw_properties` and on typed fields where we model
them.

References:
  * RFC 9253 §5 — LINK property.
  * RFC 9253 §4.2 — GAP parameter on RELATED-TO.
  * RFC 9253 §7 — expanded RELTYPE values.
  * RFC 9253 §6 — STRUCTURED-CATEGORIES, CONCEPT, REFID.

For properties we haven't typed (LINK, STRUCTURED-CATEGORIES,
CONCEPT, REFID), the contract is that `raw_properties` preserves
them so downstream tooling can process. Typed exposure on events is
a v1.2+ enhancement.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import find_event, run_parse, wrap_event


def _event_with(props: str, uid: str = "e1") -> str:
    body = f"UID:{uid}\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n{props}"
    return wrap_event(body)


def _raw_names(ev: dict[str, Any]) -> list[str]:
    raw = cast(list[dict[str, Any]], ev.get("raw_properties") or [])
    return [str(p.get("name", "")).upper() for p in raw]


# ---------------------------------------------------------------------------
# LINK property (RFC 9253 §5)
# ---------------------------------------------------------------------------


def test_link_property_preserved_in_raw(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """LINK property with URI value is preserved in raw_properties."""
    ics = _event_with("LINK:https://example.com/docs/proposal.pdf\n")
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    assert "LINK" in _raw_names(ev)


def test_link_with_linkrel_parameter(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """LINK;LINKREL=x-name preserves the parameter."""
    ics = _event_with(
        "LINK;LINKREL=CHILD;VALUE=URI:https://example.com/child.ics\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    raw = cast(list[dict[str, Any]], ev.get("raw_properties") or [])
    link = next((p for p in raw if str(p.get("name", "")).upper() == "LINK"), None)
    assert link is not None
    params = link.get("params", {})
    assert isinstance(params, dict)
    assert params.get("LINKREL") == "CHILD"


# ---------------------------------------------------------------------------
# GAP parameter on RELATED-TO (RFC 9253 §4.2)
# ---------------------------------------------------------------------------


def test_related_to_gap_parameter(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RELATED-TO;GAP=PT30M preserves the GAP duration."""
    ics = _event_with(
        "RELATED-TO;RELTYPE=FINISHTOSTART;GAP=PT30M:other-event-uid\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    raw = cast(list[dict[str, Any]], ev.get("raw_properties") or [])
    rel = next(
        (p for p in raw if str(p.get("name", "")).upper() == "RELATED-TO"), None
    )
    assert rel is not None
    params = rel.get("params", {})
    assert isinstance(params, dict)
    assert params.get("GAP") == "PT30M"
    assert params.get("RELTYPE") == "FINISHTOSTART"


# ---------------------------------------------------------------------------
# Expanded RELTYPE values (RFC 9253 §7)
# ---------------------------------------------------------------------------


def test_reltype_finishtofinish(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    ics = _event_with(
        "RELATED-TO;RELTYPE=FINISHTOFINISH:other-uid\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    raw = cast(list[dict[str, Any]], ev.get("raw_properties") or [])
    rel = next(
        (p for p in raw if str(p.get("name", "")).upper() == "RELATED-TO"), None
    )
    assert rel is not None
    assert rel["params"].get("RELTYPE") == "FINISHTOFINISH"


def test_reltype_dependson(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    ics = _event_with("RELATED-TO;RELTYPE=DEPENDS-ON:prerequisite\n")
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    raw = cast(list[dict[str, Any]], ev.get("raw_properties") or [])
    rel = next(
        (p for p in raw if str(p.get("name", "")).upper() == "RELATED-TO"), None
    )
    assert rel is not None
    assert rel["params"].get("RELTYPE") == "DEPENDS-ON"


# ---------------------------------------------------------------------------
# STRUCTURED-CATEGORIES (RFC 9253 §6.2)
# ---------------------------------------------------------------------------


def test_structured_categories_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """STRUCTURED-CATEGORIES carries hierarchical category URIs."""
    ics = _event_with(
        "STRUCTURED-CATEGORIES:http://example.com/category/tree/project/alpha\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    assert "STRUCTURED-CATEGORIES" in _raw_names(ev)


# ---------------------------------------------------------------------------
# CONCEPT / REFID (RFC 9253 §6.3 / §6.4)
# ---------------------------------------------------------------------------


def test_concept_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    ics = _event_with(
        "CONCEPT:http://example.com/concepts/project-milestone\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    assert "CONCEPT" in _raw_names(ev)


def test_refid_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    ics = _event_with("REFID:external-ref-ABC123\n")
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    assert "REFID" in _raw_names(ev)


# ---------------------------------------------------------------------------
# RELATED-TO as a typed field on VEVENT / VJOURNAL (RFC 5545 §3.8.4.5).
# Codex iter 4 called out that the schema claimed a typed `related_to` on
# journals but the impl only parsed RELATED-TO inside VALARM. These tests
# pin the structured shape `{value, reltype}` — matching VALARM.
# ---------------------------------------------------------------------------


def test_event_related_to_surfaced_as_typed_field(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """RELATED-TO on VEVENT MUST populate a typed `related_to` array
    with the same `{value, reltype}` shape VALARM uses. The raw
    property is also preserved but the typed view is what downstream
    tooling relies on."""
    ics = _event_with(
        "RELATED-TO;RELTYPE=PARENT:parent-event-uid-123\n"
        "RELATED-TO:sibling-uid-456\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    ev = find_event(out, "e1")
    rels = cast(list[dict[str, Any]], ev.get("related_to") or [])
    assert len(rels) == 2, (
        f"expected 2 RELATED-TO entries; got {rels!r}"
    )
    # First entry: explicit RELTYPE=PARENT.
    assert rels[0].get("value") == "parent-event-uid-123"
    assert rels[0].get("reltype") == "PARENT"
    # Second entry: no RELTYPE → null (RFC 5545 default is PARENT
    # semantically but we surface only the wire-present value).
    assert rels[1].get("value") == "sibling-uid-456"
    assert rels[1].get("reltype") is None


def test_journal_related_to_surfaced_as_typed_field(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """VJOURNAL must also surface `related_to` as a typed array of
    `{value, reltype}` objects — iter 4 flagged this as missing from
    the parser (only VALARM had it)."""
    ics = (
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//T//EN\n"
        "BEGIN:VJOURNAL\n"
        "UID:j1\nDTSTAMP:20260101T120000Z\n"
        "DTSTART:20260301T100000Z\nSUMMARY:Retro notes\n"
        "RELATED-TO;RELTYPE=CHILD:notes-page-2\n"
        "END:VJOURNAL\n"
        "END:VCALENDAR\n"
    )
    out = run_parse(submission_command, ics, tmp_path)
    journals = cast(list[dict[str, Any]], out.get("journals") or [])
    assert len(journals) == 1
    rels = cast(list[dict[str, Any]], journals[0].get("related_to") or [])
    assert len(rels) == 1
    assert rels[0].get("value") == "notes-page-2"
    assert rels[0].get("reltype") == "CHILD"
