"""Helpers for crafting and inspecting raw IGES physical records in tests."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path


def hollerith(text: str) -> str:
    """Encode ``text`` as an IGES Hollerith string."""
    return f"{len(text)}H{text}"


def build_global_payload(
    fields: Sequence[str],
    *,
    param_delimiter: str = ",",
    record_delimiter: str = ";",
) -> str:
    """Build a raw Global-section payload from fields 3..26."""
    if len(fields) != 24:
        raise ValueError(f"expected 24 global fields, got {len(fields)}")
    return param_delimiter.join([
        hollerith(param_delimiter),
        hollerith(record_delimiter),
        *fields,
    ]) + record_delimiter


def pad_iges_line(data: str, section: str, seq: int) -> str:
    """Pad ``data`` to columns 1-72, then append section letter + sequence."""
    return f"{data.ljust(72)[:72]}{section}{seq:>7d}"


def make_empty_iges(
    global_payload: str,
    *,
    start_lines: Sequence[str] | None = None,
) -> str:
    """Construct a Start/Global/Terminate-only IGES document."""
    starts = list(start_lines or ["pytest fixture"])
    s_lines = [pad_iges_line(line, "S", i + 1) for i, line in enumerate(starts)]
    g_lines = [
        pad_iges_line(global_payload[i:i + 72], "G", (i // 72) + 1)
        for i in range(0, len(global_payload), 72)
    ]
    t_body = f"S{len(s_lines):>7d}G{len(g_lines):>7d}D{0:>7d}P{0:>7d}"
    t_line = pad_iges_line(t_body, "T", 1)
    return "\n".join([*s_lines, *g_lines, t_line]) + "\n"


def read_physical_lines(path: Path) -> list[str]:
    """Read an IGES file as 80-column physical records."""
    return path.read_text(encoding="latin-1").splitlines()


def physical_lines_by_section(path: Path) -> dict[str, list[str]]:
    """Group physical records by their section code in column 73."""
    grouped: defaultdict[str, list[str]] = defaultdict(list)
    for line in read_physical_lines(path):
        if len(line) < 73:
            continue
        grouped[line[72]].append(line)
    return dict(grouped)


def parse_terminate_counts(line: str) -> Mapping[str, int]:
    """Parse the S/G/D/P counts from a Terminate-section physical record."""
    match = re.fullmatch(r"S[ ]*(\d+)G[ ]*(\d+)D[ ]*(\d+)P[ ]*(\d+)", line[:32])
    if match is None:
        raise ValueError(f"not a terminate record: {line!r}")
    return {
        "S": int(match.group(1)),
        "G": int(match.group(2)),
        "D": int(match.group(3)),
        "P": int(match.group(4)),
    }
