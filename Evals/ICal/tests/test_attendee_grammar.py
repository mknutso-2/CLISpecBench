"""Cal-address parameter grammar for ATTENDEE per RFC 5545 §3.2.2-§3.2.18 and §3.8.4.1.

ATTENDEE values are CAL-ADDRESS URIs (most commonly `mailto:` form). The
full set of parameters that may appear on an ATTENDEE property:

  * §3.2.2  CN               common name (text)
  * §3.2.3  CUTYPE           INDIVIDUAL | GROUP | RESOURCE | ROOM | UNKNOWN | x-name
  * §3.2.4  DELEGATED-FROM   quoted list of cal-addresses
  * §3.2.5  DELEGATED-TO     quoted list of cal-addresses
  * §3.2.6  DIR              quoted URI
  * §3.2.10 LANGUAGE         RFC-5646 language tag
  * §3.2.11 MEMBER           quoted list of cal-addresses
  * §3.2.12 PARTSTAT         NEEDS-ACTION | ACCEPTED | DECLINED | TENTATIVE |
                              DELEGATED | COMPLETED | IN-PROCESS | x-name
  * §3.2.16 ROLE             CHAIR | REQ-PARTICIPANT | OPT-PARTICIPANT |
                              NON-PARTICIPANT | x-name
  * §3.2.17 RSVP             TRUE | FALSE (boolean)
  * §3.2.18 SENT-BY          quoted cal-address

Each ATTENDEE parses into a cal-address object:

    {"value": "mailto:…", "cn", "cutype", "role", "partstat", "rsvp",
     "member", "delegated_from", "delegated_to", "sent_by", "dir", "language"}

The tests here exercise normal cases, edge cases (quoted lists, case,
defaults), and invalid cases (malformed parameter values).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from conftest import find_event, run_parse, wrap_event


def _attendees(ev: dict[str, Any]) -> list[dict[str, Any]]:
    atts = ev.get("attendees")
    assert isinstance(atts, list), f"event missing attendees array; got {list(ev)}"
    return cast(list[dict[str, Any]], atts)


def _wrap_attendee(line: str) -> str:
    return wrap_event("UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n" + line + "\n")


# --- Value / URI handling ---


def test_attendee_value_is_cal_address_uri(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.8.4.1: ATTENDEE value is a CAL-ADDRESS URI. `value` holds the URI verbatim."""
    ics = _wrap_attendee("ATTENDEE:mailto:jane@example.com")
    out = run_parse(submission_command, ics, tmp_path)
    att = _attendees(find_event(out, "e1"))[0]
    assert att.get("value") == "mailto:jane@example.com"


def test_attendee_non_mailto_scheme(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.3.3: cal-address is a URI; non-mailto schemes are permitted and preserved."""
    ics = _wrap_attendee("ATTENDEE:http://example.com/people/jane")
    out = run_parse(submission_command, ics, tmp_path)
    att = _attendees(find_event(out, "e1"))[0]
    assert att["value"] == "http://example.com/people/jane"


# --- CN (§3.2.2) ---


def test_cn_unquoted(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.2.2: CN is text, not restricted to quoted-string unless it contains DQUOTE-only chars."""
    ics = _wrap_attendee("ATTENDEE;CN=Jane Doe:mailto:jane@example.com")
    out = run_parse(submission_command, ics, tmp_path)
    assert _attendees(find_event(out, "e1"))[0].get("cn") == "Jane Doe"


def test_cn_quoted_with_comma(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.1.1 quoted-string preserves COMMA inside CN."""
    ics = _wrap_attendee('ATTENDEE;CN="Smith, John":mailto:j@example.com')
    out = run_parse(submission_command, ics, tmp_path)
    assert _attendees(find_event(out, "e1"))[0].get("cn") == "Smith, John"


# --- CUTYPE (§3.2.3) ---


def test_cutype_group(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.2.3: CUTYPE=GROUP surfaces verbatim."""
    ics = _wrap_attendee("ATTENDEE;CUTYPE=GROUP:mailto:team@example.com")
    out = run_parse(submission_command, ics, tmp_path)
    assert _attendees(find_event(out, "e1"))[0].get("cutype") == "GROUP"


def test_cutype_room(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.2.3: CUTYPE=ROOM for a meeting room resource."""
    ics = _wrap_attendee("ATTENDEE;CUTYPE=ROOM:mailto:conf-a@example.com")
    out = run_parse(submission_command, ics, tmp_path)
    assert _attendees(find_event(out, "e1"))[0].get("cutype") == "ROOM"


# --- ROLE (§3.2.16) ---


def test_role_chair(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.2.16: ROLE=CHAIR."""
    ics = _wrap_attendee("ATTENDEE;ROLE=CHAIR:mailto:boss@example.com")
    out = run_parse(submission_command, ics, tmp_path)
    assert _attendees(find_event(out, "e1"))[0].get("role") == "CHAIR"


def test_role_opt_participant_hyphen_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.2.16: ROLE=OPT-PARTICIPANT survives verbatim with the hyphen."""
    ics = _wrap_attendee("ATTENDEE;ROLE=OPT-PARTICIPANT:mailto:opt@example.com")
    out = run_parse(submission_command, ics, tmp_path)
    assert _attendees(find_event(out, "e1"))[0].get("role") == "OPT-PARTICIPANT"


# --- PARTSTAT (§3.2.12) ---


def test_partstat_needs_action(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.2.12: PARTSTAT=NEEDS-ACTION preserves the hyphen."""
    ics = _wrap_attendee("ATTENDEE;PARTSTAT=NEEDS-ACTION:mailto:x@example.com")
    out = run_parse(submission_command, ics, tmp_path)
    assert _attendees(find_event(out, "e1"))[0].get("partstat") == "NEEDS-ACTION"


# --- RSVP (§3.2.17) ---


def test_rsvp_true_becomes_boolean(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.2.17: RSVP=TRUE → boolean true (not the string "TRUE")."""
    ics = _wrap_attendee("ATTENDEE;RSVP=TRUE:mailto:a@example.com")
    out = run_parse(submission_command, ics, tmp_path)
    assert _attendees(find_event(out, "e1"))[0].get("rsvp") is True


def test_rsvp_false_becomes_boolean(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.2.17: RSVP=FALSE → boolean false (not the string "FALSE" or null)."""
    ics = _wrap_attendee("ATTENDEE;RSVP=FALSE:mailto:a@example.com")
    out = run_parse(submission_command, ics, tmp_path)
    assert _attendees(find_event(out, "e1"))[0].get("rsvp") is False


# --- MEMBER (§3.2.11) ---


def test_member_single_quoted(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.2.11: MEMBER = DQUOTE cal-address DQUOTE. Single member becomes one-element list."""
    ics = _wrap_attendee('ATTENDEE;MEMBER="mailto:team@example.com":mailto:alice@example.com')
    out = run_parse(submission_command, ics, tmp_path)
    att = _attendees(find_event(out, "e1"))[0]
    assert att.get("member") == ["mailto:team@example.com"]


def test_member_multiple_comma_separated(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.2.11: multiple members as comma-separated quoted strings."""
    ics = _wrap_attendee(
        'ATTENDEE;MEMBER="mailto:projA@example.com","mailto:projB@example.com":'
        "mailto:alice@example.com"
    )
    out = run_parse(submission_command, ics, tmp_path)
    att = _attendees(find_event(out, "e1"))[0]
    assert att.get("member") == [
        "mailto:projA@example.com",
        "mailto:projB@example.com",
    ]


# --- DELEGATED-FROM / DELEGATED-TO (§3.2.4, §3.2.5) ---


def test_delegated_from(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.2.4: DELEGATED-FROM is a quoted list; surface as `delegated_from`."""
    ics = _wrap_attendee(
        'ATTENDEE;DELEGATED-FROM="mailto:orig@example.com":mailto:delegate@example.com'
    )
    out = run_parse(submission_command, ics, tmp_path)
    att = _attendees(find_event(out, "e1"))[0]
    assert att.get("delegated_from") == ["mailto:orig@example.com"]


def test_delegated_to_multiple(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.2.5: DELEGATED-TO accepts a comma-separated quoted list."""
    ics = _wrap_attendee(
        'ATTENDEE;DELEGATED-TO="mailto:a@example.com","mailto:b@example.com":'
        "mailto:orig@example.com"
    )
    out = run_parse(submission_command, ics, tmp_path)
    att = _attendees(find_event(out, "e1"))[0]
    assert att.get("delegated_to") == [
        "mailto:a@example.com",
        "mailto:b@example.com",
    ]


# --- DIR (§3.2.6) ---


def test_dir_quoted_uri(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.2.6: DIR is a DQUOTE-wrapped URI. The quotes are removed by the parser."""
    ics = _wrap_attendee('ATTENDEE;DIR="ldap://example.com:6666/o=ABC,c=US":mailto:jim@example.com')
    out = run_parse(submission_command, ics, tmp_path)
    att = _attendees(find_event(out, "e1"))[0]
    assert att.get("dir") == "ldap://example.com:6666/o=ABC,c=US"


# --- SENT-BY (§3.2.18) ---


def test_sent_by(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.2.18: SENT-BY holds a mailto URI as a quoted-string. Quotes stripped."""
    ics = _wrap_attendee('ATTENDEE;SENT-BY="mailto:assistant@example.com":mailto:boss@example.com')
    out = run_parse(submission_command, ics, tmp_path)
    att = _attendees(find_event(out, "e1"))[0]
    assert att.get("sent_by") == "mailto:assistant@example.com"


# --- LANGUAGE (§3.2.10) ---


def test_language_tag(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.2.10: LANGUAGE holds an RFC-5646 language tag; surface verbatim."""
    ics = _wrap_attendee('ATTENDEE;LANGUAGE=en-US;CN="Jane":mailto:jane@example.com')
    out = run_parse(submission_command, ics, tmp_path)
    att = _attendees(find_event(out, "e1"))[0]
    assert att.get("language") == "en-US"


# --- Combined / folded ---


def test_combined_parameters_all(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.8.4.1: full parameter set on a single ATTENDEE parses cleanly."""
    ics = _wrap_attendee(
        'ATTENDEE;CN="Jane Doe";CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;'
        "PARTSTAT=ACCEPTED;RSVP=TRUE;"
        'DELEGATED-FROM="mailto:orig@example.com";'
        'SENT-BY="mailto:assistant@example.com";'
        "LANGUAGE=en:mailto:jane@example.com"
    )
    out = run_parse(submission_command, ics, tmp_path)
    att = _attendees(find_event(out, "e1"))[0]
    assert att.get("cn") == "Jane Doe"
    assert att.get("cutype") == "INDIVIDUAL"
    assert att.get("role") == "REQ-PARTICIPANT"
    assert att.get("partstat") == "ACCEPTED"
    assert att.get("rsvp") is True
    assert att.get("delegated_from") == ["mailto:orig@example.com"]
    assert att.get("sent_by") == "mailto:assistant@example.com"
    assert att.get("language") == "en"
    assert att.get("value") == "mailto:jane@example.com"


def test_folded_attendee_across_lines(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.1 content line folding: parameters may span folded lines without loss."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "ATTENDEE;ROLE=REQ-PARTICIPANT;DELEGATED-FROM=\n"
        ' "mailto:boss@example.com";PARTSTAT=ACCEPTED;CN=Jane Doe:mailto:\n'
        " jdoe@example.com\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    att = _attendees(find_event(out, "e1"))[0]
    assert att.get("cn") == "Jane Doe"
    assert att.get("value") == "mailto:jdoe@example.com"
    assert att.get("delegated_from") == ["mailto:boss@example.com"]


def test_multiple_attendees_order_preserved(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.8.4.1: multiple ATTENDEE properties produce a list in source order."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        "ATTENDEE;CN=First:mailto:first@example.com\n"
        "ATTENDEE;CN=Second:mailto:second@example.com\n"
        "ATTENDEE;CN=Third:mailto:third@example.com\n"
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    atts = _attendees(find_event(out, "e1"))
    assert [a.get("cn") for a in atts] == ["First", "Second", "Third"]


# --- Defaults for missing params ---


def test_absent_params_are_null_or_missing(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """An attendee with only the cal-address URI has null/absent for all params."""
    ics = _wrap_attendee("ATTENDEE:mailto:bare@example.com")
    out = run_parse(submission_command, ics, tmp_path)
    att = _attendees(find_event(out, "e1"))[0]
    assert att.get("value") == "mailto:bare@example.com"
    # All optional params missing → null (or list-valued params empty).
    assert att.get("cn") is None
    assert att.get("role") is None
    assert att.get("rsvp") is None
    assert att.get("cutype") is None
    # List-valued params are empty lists, not null.
    member = att.get("member")
    assert member in (None, [])
    d_from = att.get("delegated_from")
    assert d_from in (None, [])
    d_to = att.get("delegated_to")
    assert d_to in (None, [])


# --- Case insensitivity of parameter names ---


def test_parameter_name_case_insensitive(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.1: parameter names are case-insensitive: `cn=` == `CN=` == `Cn=`."""
    ics = _wrap_attendee("ATTENDEE;cn=Jane;Role=CHAIR:mailto:jane@example.com")
    out = run_parse(submission_command, ics, tmp_path)
    att = _attendees(find_event(out, "e1"))[0]
    assert att.get("cn") == "Jane"
    assert att.get("role") == "CHAIR"


# --- Invalid / experimental tokens (§3.2.3, §3.2.12, §3.2.16) ---


def test_cutype_x_name_passthrough(submission_command: tuple[str, ...], tmp_path: Path) -> None:
    """§3.2.3 + §3.2.16: experimental (x-name) or unknown IANA tokens on
    CUTYPE / ROLE must round-trip, not be dropped or validated away."""
    ics = _wrap_attendee("ATTENDEE;CUTYPE=X-ROBOT;ROLE=REVIEWER:mailto:bot@example.com")
    out = run_parse(submission_command, ics, tmp_path)
    att = _attendees(find_event(out, "e1"))[0]
    assert att.get("cutype") == "X-ROBOT"
    assert att.get("role") == "REVIEWER"


# --- Organizer uses same cal-address object ---


def test_organizer_uses_cal_address_object(
    submission_command: tuple[str, ...], tmp_path: Path
) -> None:
    """§3.8.4.3: ORGANIZER carries the same cal-address grammar. It must be an
    object of the same shape as ATTENDEE, not a bare string."""
    body = (
        "UID:e1\nDTSTAMP:20260101T120000Z\nDTSTART:20260301T100000Z\n"
        'ORGANIZER;CN="Boss";SENT-BY="mailto:sec@example.com":mailto:boss@example.com\n'
    )
    out = run_parse(submission_command, wrap_event(body), tmp_path)
    org_raw = find_event(out, "e1").get("organizer")
    assert isinstance(org_raw, dict), f"organizer must be an object; got {type(org_raw).__name__}"
    org = cast(dict[str, Any], org_raw)
    assert org.get("value") == "mailto:boss@example.com"
    assert org.get("cn") == "Boss"
    assert org.get("sent_by") == "mailto:sec@example.com"
