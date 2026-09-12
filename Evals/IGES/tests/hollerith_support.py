"""Independent physical string checks for §2.2.2.3, without a reference parser."""

from __future__ import annotations

import re


def assert_legal_hollerith_counts(payload: str, pd: str = ",", rd: str = ";") -> None:
    """Scan complete free-form fields, preserving delimiters inside strings."""
    i = 0
    while i < len(payload):
        while i < len(payload) and payload[i] == " ":
            i += 1
        match = re.match(r"([0-9]+)[Hh]", payload[i:])
        if match:
            count = int(match[1])
            assert count > 0, "§2.2.2.3 requires a nonzero Hollerith character count"
            i += len(match[0]) + count
            assert i <= len(payload), "Hollerith content exceeds available physical data"
            while i < len(payload) and payload[i] == " ":
                i += 1
        else:
            while i < len(payload) and payload[i] not in (pd, rd):
                i += 1
        assert i < len(payload) and payload[i] in (pd, rd), "missing field delimiter"
        if payload[i] == rd:
            # Public §4 free-format rules permit trailing comments after rd.
            return
        i += 1
    raise AssertionError("missing record terminator")
