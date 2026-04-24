"""Byte-exact `.bbl` parity tests against the four canonical reference styles.

For each of `plain.bst` / `alpha.bst` / `unsrt.bst` / `abbrv.bst`, this
test runs the submission against a curated `refs.bib` + `refs.cites`
and asserts the submission's `.bbl` output matches a known-good
artifact under `tests/fixtures/`.

The `.expected.bbl` fixtures committed in the repository are the
contract. They should be regenerated from the historic BibTeX 0.99c
binary (see `Evals/BibTeX/tools/regenerate_bbl_fixtures.sh` —
supports a Docker `texlive/texlive` image). Initial fixtures may be
seeded from the repo's reference implementation; any bug in the
reference impl relative to BibTeX 0.99c surfaces as a test failure
that must be resolved by fixing the impl and regenerating fixtures.

These four tests are the **single largest discriminator** in the
BibTeX eval: a correct interpreter of the `.bst` stack machine
against realistic inputs must reproduce BibTeX's output.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).parent
FIXTURES = HERE / "fixtures"
# Reference styles live in the eval's docs/authoritative/.
STYLES_DIR = HERE.parent / "prompt" / "docs" / "authoritative"


REFERENCE_STYLES = ["plain", "alpha", "unsrt", "abbrv"]


@pytest.mark.parametrize("style", REFERENCE_STYLES)
def test_reference_style_bbl_parity(
    submission_command: tuple[str, ...], tmp_path: Path, style: str
) -> None:
    """Byte-exact `.bbl` parity for one of the four canonical styles.

    Runs the submission against `fixtures/refs.bib` + `fixtures/refs.cites`
    with `authoritative/<style>.bst` and compares the produced `.bbl`
    against `fixtures/<style>.expected.bbl` byte-by-byte.
    """
    bib_file = FIXTURES / "refs.bib"
    cites_file = FIXTURES / "refs.cites"
    style_file = STYLES_DIR / f"{style}.bst"
    expected_file = FIXTURES / f"{style}.expected.bbl"

    for required in (bib_file, cites_file, style_file, expected_file):
        assert required.exists(), f"fixture missing: {required}"

    output_file = tmp_path / f"out.{style}.bbl"

    args = [
        *submission_command,
        "--bib",
        str(bib_file),
        "--style",
        str(style_file),
        "--cites",
        str(cites_file),
        "--output",
        str(output_file),
    ]
    result = subprocess.run(args, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, (
        f"bibtex exited with {result.returncode} (expected 0)\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert output_file.exists(), f"submission produced no output file: {output_file}"

    actual = output_file.read_bytes()
    expected = expected_file.read_bytes()
    if actual == expected:
        return

    # Produce a readable diff on mismatch so the failure localizes quickly.
    actual_text = actual.decode("utf-8", errors="replace")
    expected_text = expected.decode("utf-8", errors="replace")
    actual_lines = actual_text.splitlines(keepends=True)
    expected_lines = expected_text.splitlines(keepends=True)
    # Show first divergence:
    max_len = max(len(actual_lines), len(expected_lines))
    for i in range(max_len):
        a = actual_lines[i] if i < len(actual_lines) else "<EOF>"
        e = expected_lines[i] if i < len(expected_lines) else "<EOF>"
        if a != e:
            raise AssertionError(
                f"{style}.bst .bbl parity failure at line {i + 1}:\n"
                f"  expected: {e!r}\n"
                f"  actual:   {a!r}\n"
                f"(bbl sizes: actual={len(actual)}, expected={len(expected)})"
            )
    raise AssertionError(
        f"{style}.bst .bbl byte-mismatch but line-by-line compare found "
        f"no difference (possible trailing-newline or CRLF issue). "
        f"Sizes: actual={len(actual)}, expected={len(expected)}."
    )
