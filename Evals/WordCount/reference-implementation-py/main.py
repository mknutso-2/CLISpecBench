"""WordCount reference implementation (Python).

Mirrors the behavior expected by Evals/WordCount/tests:
- Character count is the raw byte length of the file (not codepoints).
- Line count is the number of '\n' bytes (a trailing line without '\n' still
  counts as 1 line when the file is non-empty).
- Words are whitespace-delimited tokens; punctuation is attached to words.
- Unique-word counts are case-insensitive; top_words emits lowercase forms.
- top_words is ordered by descending count, then alphabetically by word,
  with at most 10 entries.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_WHITESPACE = frozenset(b" \t\n\r\f\v")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="wordcount")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def _count_lines(data: bytes) -> int:
    if not data:
        return 0
    newlines = data.count(b"\n")
    if data.endswith(b"\n"):
        return newlines
    return newlines + 1


def _split_words(data: bytes) -> list[str]:
    words: list[str] = []
    current: bytearray = bytearray()
    for byte in data:
        if byte in _WHITESPACE:
            if current:
                words.append(current.decode("utf-8", errors="replace"))
                current = bytearray()
        else:
            current.append(byte)
    if current:
        words.append(current.decode("utf-8", errors="replace"))
    return words


def _analyze(data: bytes) -> dict[str, Any]:
    words = _split_words(data)
    lowered = [word.lower() for word in words]
    counts = Counter(lowered)

    top = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:10]

    return {
        "lines": _count_lines(data),
        "words": len(words),
        "characters": len(data),
        "unique_words": len(counts),
        "top_words": [{"word": word, "count": count} for word, count in top],
    }


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit:
        return 1

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        data = input_path.read_bytes()
    except OSError:
        return 1

    try:
        result = _analyze(data)
    except Exception:
        return 2

    try:
        output_path.write_text(
            json.dumps(result, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
