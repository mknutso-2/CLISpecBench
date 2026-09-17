"""Writer-format tests for Hollerith, real, and logical output."""

# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from iges_support import make_entity, single_line_document, wrap_entities, write_iges_from_json
from raw_iges_support import physical_lines_by_section
from topology_support import open_triangle_document


def test_global_strings_use_hollerith_encoding_in_g_section(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities([])
    doc["global"]["author"] = "Jane Doe"
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="global-hollerith")

    g_body = "".join(line[:72] for line in physical_lines_by_section(iges_path)["G"])
    assert "8HJane Doe" in g_body


_REAL_TOKEN_RE = re.compile(
    # §2.2.2.2: a real literal must contain a decimal point or an
    # exponent (not both optional). We accept the sign-integer-decimal-
    # fractional-exponent union:
    #   [±] (digits . [digits] | . digits | digits)  ( [DE] [±] digits )?
    # with the constraint that decimal-point-or-exponent is present.
    r"^[+-]?(?:"
    r"\d+\.\d*|\.\d+|\d+\.|"  # forms containing a decimal point
    r"\d+(?=[eEdD])"  # integer form, must be followed by exponent
    r")(?:[eEdD][+-]?\d+)?$"
)


def _iter_pd_value_tokens(p_body: str) -> list[str]:
    # Strip the entity-type prefix and record terminator, then split on
    # the parameter delimiter. Assumes default delimiters (`,` / `;`)
    # and a single-line PD record; that matches the Line-only fixture
    # used by the caller.
    assert p_body.endswith(";"), p_body
    body = p_body[:-1]
    fields = body.split(",")
    # Drop the entity-type prefix (first field, e.g. "110").
    return fields[1:]


def test_real_values_in_parameter_records_are_spec_legal(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    """§2.2.2.2: a real literal must contain a decimal point or an
    exponent. This test verifies each coordinate the Line writer emits
    is both numerically correct AND matches one of the spec-legal real
    encodings — not just the `"1."` / `"1.0"` form the reference impls
    happen to prefer."""
    iges_path = write_iges_from_json(
        submission_command,
        single_line_document((1.0, 2.0, 3.0), (4.0, 5.0, 6.0)),
        tmp_path,
        name="real-format",
    )

    p_body = physical_lines_by_section(iges_path)["P"][0][:64].rstrip()
    tokens = _iter_pd_value_tokens(p_body)
    assert len(tokens) == 6, tokens
    expected = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    for tok, want in zip(tokens, expected, strict=True):
        assert _REAL_TOKEN_RE.match(tok), f"{tok!r} is not a spec-legal real literal (§2.2.2.2)"
        # Allow the IGES D exponent for double precision.
        got = float(tok.replace("D", "E").replace("d", "e"))
        assert got == want, f"token {tok!r} decodes to {got}, expected {want}"


def test_string_values_in_parameter_records_use_hollerith_encoding(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    doc = wrap_entities(
        [
            make_entity(
                de_index=1,
                entity_type=308,
                data={"depth": 1, "name": "NETLIST", "n": 0, "entities": []},
            ),
        ]
    )
    iges_path = write_iges_from_json(submission_command, doc, tmp_path, name="pd-hollerith")

    p_body = physical_lines_by_section(iges_path)["P"][0][:64].rstrip()
    assert "7HNETLIST" in p_body


def test_logical_values_in_parameter_records_use_zero_and_one(
    submission_command: Sequence[str], tmp_path: Path
) -> None:
    # §4.146 requires a real surface, N > 0 loops and a Shell parent. An
    # empty Face is invalid before its boolean encoding can be observed.
    # Reuse the independently validated topology; do not parse/evaluate it
    # through the submission or assert unrelated supporting entity fields.
    doc, ids = open_triangle_document()
    face = next(record for record in doc["entities"] if record["de_index"] == ids["face"])
    for flag in (True, False):
        # Both values are legal: false leaves the outer loop undesignated.
        face["entity"]["data"]["outer_loop_flag"] = flag
        iges_path = write_iges_from_json(
            submission_command, doc, tmp_path, name=f"logical-format-{int(flag)}"
        )
        # A writer may renumber DEs and split parameter data across lines.
        # Group by the physical owner and identify the sole Face by type.
        by_owner: dict[int, str] = {}
        for line in physical_lines_by_section(iges_path)["P"]:
            owner = int(line[64:72])
            by_owner[owner] = by_owner.get(owner, "") + line[:64]
        fields = next(
            body.split(";", 1)[0].split(",")
            for body in by_owner.values()
            if int(body.split(",", 1)[0].strip()) == 510
        )
        token = fields[3].strip()
        # §§2.2.2.6/2.2.3: unsigned integer 1/0, with an empty field also
        # permitted for implicit FALSE. Ignore legal trailing comments and
        # unrelated field encodings; real literals and TRUE/FALSE must fail.
        if not flag and not token:
            continue
        assert re.fullmatch(r"[0-9]+", token), f"Invalid Logical token: {token!r}"
        assert int(token) == int(flag), f"Wrong Logical value: {token!r}"
