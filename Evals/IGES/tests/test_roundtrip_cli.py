"""End-to-end round-trip tests for the ``iges roundtrip`` subcommand.

Asserts that ``iges roundtrip`` on each reference fixture produces a
file that re-parses successfully and yields the same parsed entity count.
The first pass may normalize defaulted Global delimiters and expand
two-digit year timestamps (see the 2026-04-14 port history), but
once a file has been normalized, a second ``iges roundtrip`` pass must
be byte-identical to the first.

Ports ``Evals/IGES-SDK/tests/spec/test_file_roundtrip.cpp`` /
``test_writer_roundtrip*.cpp``.
"""

# pyright: reportUnknownMemberType=none
# pyright: reportUnknownVariableType=none
# pyright: reportUnknownArgumentType=none
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from iges_support import parse_iges_to_json, roundtrip_iges

FIXTURES = Path(__file__).parent / "data"


@pytest.mark.parametrize(
    ("name", "expected_count"),
    [
        ("ex1.iges", 21),
        ("ex2.iges", 90),
        ("ex3.iges", 109),
    ],
)
def test_roundtrip_fixture_preserves_entity_count(
    submission_command: Sequence[str],
    tmp_path: Path,
    name: str,
    expected_count: int,
) -> None:
    src = FIXTURES / name
    rt_path = roundtrip_iges(submission_command, src, tmp_path, name=name)

    original = parse_iges_to_json(submission_command, src, tmp_path, name=f"{name}-orig")
    reparsed = parse_iges_to_json(submission_command, rt_path, tmp_path, name=f"{name}-rt")

    assert len(original["entities"]) == expected_count
    assert len(reparsed["entities"]) == expected_count


@pytest.mark.parametrize(
    "name",
    ["ex1.iges", "ex2.iges", "ex3.iges"],
)
def test_roundtrip_fixture_preserves_entity_data(
    submission_command: Sequence[str],
    tmp_path: Path,
    name: str,
) -> None:
    """Semantic equivalence: every entity.data block matches after a
    full parse → write → parse cycle."""
    src = FIXTURES / name
    rt_path = roundtrip_iges(submission_command, src, tmp_path, name=name)

    original = parse_iges_to_json(submission_command, src, tmp_path, name=f"{name}-orig")
    reparsed = parse_iges_to_json(submission_command, rt_path, tmp_path, name=f"{name}-rt")

    for orig, rt in zip(original["entities"], reparsed["entities"], strict=True):
        assert orig["entity"]["type"] == rt["entity"]["type"]
        assert orig["entity"]["form"] == rt["entity"]["form"]
        assert orig["entity"]["data"] == rt["entity"]["data"]


@pytest.mark.parametrize("name", ["ex1.iges", "ex2.iges", "ex3.iges"])
def test_roundtrip_is_idempotent(
    submission_command: Sequence[str],
    tmp_path: Path,
    name: str,
) -> None:
    """Writer output is stable under repeated round-trip: once the file
    has been normalized, running ``iges roundtrip`` again must produce
    byte-identical output. (The first pass may normalize defaulted
    Global delimiters; subsequent passes should be fixed points.)"""
    src = FIXTURES / name
    first = roundtrip_iges(submission_command, src, tmp_path, name=f"{name}-1")
    second = roundtrip_iges(submission_command, first, tmp_path, name=f"{name}-2")

    assert first.read_bytes() == second.read_bytes()
