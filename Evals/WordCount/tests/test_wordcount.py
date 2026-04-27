"""Tests for the WordCount tool, derived from wordcount-spec.md."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from conftest import run_wordcount

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WordCountCase = tuple[str, str, dict[str, Any]]


def _run(submission_command: tuple[str, ...], text: str, tmp_path: Path) -> dict[str, Any]:
    return run_wordcount(submission_command, text, tmp_path)


# ---------------------------------------------------------------------------
# Edge cases: empty and whitespace-only files
# ---------------------------------------------------------------------------


class TestEmptyFile:
    def test_empty_file(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        result = _run(submission_command, "", tmp_path)
        assert result["lines"] == 0
        assert result["words"] == 0
        assert result["characters"] == 0
        assert result["unique_words"] == 0
        assert result["top_words"] == []


class TestWhitespaceOnly:
    def test_spaces_only(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        result = _run(submission_command, "   ", tmp_path)
        assert result["words"] == 0
        assert result["unique_words"] == 0
        assert result["top_words"] == []
        assert result["characters"] == 3

    def test_newlines_only(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        result = _run(submission_command, "\n\n\n", tmp_path)
        assert result["lines"] == 3
        assert result["words"] == 0
        assert result["characters"] == 3

    def test_mixed_whitespace(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        result = _run(submission_command, " \t\n\r\f\v", tmp_path)
        assert result["words"] == 0
        assert result["characters"] == 6


# ---------------------------------------------------------------------------
# Line counting
# ---------------------------------------------------------------------------


class TestLineCounting:
    def test_single_line_no_newline(
        self, submission_command: tuple[str, ...], tmp_path: Path
    ) -> None:
        """'hello' (5 bytes, no newline) = 1 line."""
        result = _run(submission_command, "hello", tmp_path)
        assert result["lines"] == 1

    def test_single_line_with_newline(
        self, submission_command: tuple[str, ...], tmp_path: Path
    ) -> None:
        """'hello\\n' (6 bytes) = 1 line."""
        result = _run(submission_command, "hello\n", tmp_path)
        assert result["lines"] == 1

    def test_multiple_lines(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        result = _run(submission_command, "a\nb\nc\n", tmp_path)
        assert result["lines"] == 3

    def test_multiple_lines_no_trailing_newline(
        self, submission_command: tuple[str, ...], tmp_path: Path
    ) -> None:
        result = _run(submission_command, "a\nb\nc", tmp_path)
        assert result["lines"] == 3

    def test_consecutive_newlines(
        self, submission_command: tuple[str, ...], tmp_path: Path
    ) -> None:
        """'\\n\\n\\n' = 3 lines (spec: each \\n terminates a line)."""
        result = _run(submission_command, "\n\n\n", tmp_path)
        assert result["lines"] == 3


# ---------------------------------------------------------------------------
# Character counting (bytes)
# ---------------------------------------------------------------------------


class TestCharacterCounting:
    def test_simple(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        result = _run(submission_command, "hello", tmp_path)
        assert result["characters"] == 5

    def test_with_newline(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        result = _run(submission_command, "hello\n", tmp_path)
        assert result["characters"] == 6

    def test_with_various_whitespace(
        self, submission_command: tuple[str, ...], tmp_path: Path
    ) -> None:
        text = "a b\tc\n"
        result = _run(submission_command, text, tmp_path)
        assert result["characters"] == len(text)


# ---------------------------------------------------------------------------
# Word counting
# ---------------------------------------------------------------------------


class TestWordCounting:
    def test_single_word(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        result = _run(submission_command, "hello", tmp_path)
        assert result["words"] == 1

    def test_multiple_words(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        result = _run(submission_command, "the cat sat on the mat", tmp_path)
        assert result["words"] == 6

    def test_words_separated_by_various_whitespace(
        self, submission_command: tuple[str, ...], tmp_path: Path
    ) -> None:
        result = _run(submission_command, "a\tb\nc\rd\fe\vf", tmp_path)
        assert result["words"] == 6

    def test_leading_and_trailing_whitespace(
        self, submission_command: tuple[str, ...], tmp_path: Path
    ) -> None:
        result = _run(submission_command, "  hello world  ", tmp_path)
        assert result["words"] == 2

    def test_multiple_spaces_between_words(
        self, submission_command: tuple[str, ...], tmp_path: Path
    ) -> None:
        result = _run(submission_command, "a    b    c", tmp_path)
        assert result["words"] == 3


# ---------------------------------------------------------------------------
# Unique words and case insensitivity
# ---------------------------------------------------------------------------


class TestUniqueWords:
    def test_all_unique(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        result = _run(submission_command, "apple banana cherry", tmp_path)
        assert result["unique_words"] == 3

    def test_duplicates(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        result = _run(submission_command, "the the the", tmp_path)
        assert result["unique_words"] == 1

    def test_case_insensitive(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        """'Hello', 'HELLO', and 'hello' are the same word."""
        result = _run(submission_command, "Hello HELLO hello", tmp_path)
        assert result["unique_words"] == 1
        assert result["words"] == 3


# ---------------------------------------------------------------------------
# Punctuation is part of the word
# ---------------------------------------------------------------------------


class TestPunctuation:
    def test_punctuation_attached(
        self, submission_command: tuple[str, ...], tmp_path: Path
    ) -> None:
        """'hello,' and 'hello' are different words."""
        result = _run(submission_command, "hello hello,", tmp_path)
        assert result["unique_words"] == 2

    def test_various_punctuation(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        result = _run(submission_command, "end. end! end?", tmp_path)
        assert result["unique_words"] == 3


# ---------------------------------------------------------------------------
# top_words ordering and limits
# ---------------------------------------------------------------------------


class TestTopWords:
    def test_descending_by_count(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        text = "a a a b b c"
        result = _run(submission_command, text, tmp_path)
        top = result["top_words"]
        assert len(top) == 3
        assert top[0] == {"word": "a", "count": 3}
        assert top[1] == {"word": "b", "count": 2}
        assert top[2] == {"word": "c", "count": 1}

    def test_alphabetical_tiebreaker(
        self, submission_command: tuple[str, ...], tmp_path: Path
    ) -> None:
        text = "cherry apple banana"
        result = _run(submission_command, text, tmp_path)
        top = result["top_words"]
        assert len(top) == 3
        # All have count 1, so alphabetical order
        assert top[0]["word"] == "apple"
        assert top[1]["word"] == "banana"
        assert top[2]["word"] == "cherry"

    def test_max_ten_entries(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        # 15 unique words, only top 10 should appear
        words = [f"word{i:02d}" for i in range(15)]
        # Give each a different frequency so ordering is deterministic
        tokens: list[str] = []
        for i, w in enumerate(words):
            tokens.extend([w] * (15 - i))
        text = " ".join(tokens)
        result = _run(submission_command, text, tmp_path)
        assert len(result["top_words"]) == 10
        # First should be the most frequent
        assert result["top_words"][0]["word"] == "word00"
        assert result["top_words"][0]["count"] == 15

    def test_fewer_than_ten(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        result = _run(submission_command, "one two three", tmp_path)
        assert len(result["top_words"]) == 3

    def test_empty_top_words(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        result = _run(submission_command, "", tmp_path)
        assert result["top_words"] == []

    def test_case_insensitive_in_top_words(
        self, submission_command: tuple[str, ...], tmp_path: Path
    ) -> None:
        """Words appear as lowercase in top_words."""
        result = _run(submission_command, "Hello WORLD", tmp_path)
        words_in_top = [entry["word"] for entry in result["top_words"]]
        assert "hello" in words_in_top
        assert "world" in words_in_top
        # No uppercase forms
        for entry in result["top_words"]:
            assert entry["word"] == entry["word"].lower()


# ---------------------------------------------------------------------------
# JSON structure validation
# ---------------------------------------------------------------------------


class TestJsonStructure:
    def test_required_keys_present(
        self, submission_command: tuple[str, ...], tmp_path: Path
    ) -> None:
        result = _run(submission_command, "hello world", tmp_path)
        assert "lines" in result
        assert "words" in result
        assert "characters" in result
        assert "unique_words" in result
        assert "top_words" in result

    def test_types(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        result = _run(submission_command, "hello world", tmp_path)
        assert isinstance(result["lines"], int)
        assert isinstance(result["words"], int)
        assert isinstance(result["characters"], int)
        assert isinstance(result["unique_words"], int)
        assert isinstance(result["top_words"], list)

    def test_top_words_entry_structure(
        self, submission_command: tuple[str, ...], tmp_path: Path
    ) -> None:
        result = _run(submission_command, "hello", tmp_path)
        for entry in result["top_words"]:
            assert "word" in entry
            assert "count" in entry
            assert isinstance(entry["word"], str)
            assert isinstance(entry["count"], int)


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------


class TestExitCodes:
    def test_success_exit_code(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.json"
        input_file.write_text("hello", encoding="utf-8")
        result = __import__("subprocess").run(
            [*submission_command, "--input", str(input_file), "--output", str(output_file)],
            capture_output=True,
        )
        assert result.returncode == 0

    def test_missing_args_exit_code(
        self, submission_command: tuple[str, ...], tmp_path: Path
    ) -> None:
        result = __import__("subprocess").run(
            list(submission_command),
            capture_output=True,
        )
        assert result.returncode == 1

    def test_missing_input_file_exit_code(
        self, submission_command: tuple[str, ...], tmp_path: Path
    ) -> None:
        output_file = tmp_path / "output.json"
        result = __import__("subprocess").run(
            [
                *submission_command,
                "--input",
                str(tmp_path / "nonexistent.txt"),
                "--output",
                str(output_file),
            ],
            capture_output=True,
        )
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Integration: full document
# ---------------------------------------------------------------------------


class TestIntegration:
    def test_multiline_document(self, submission_command: tuple[str, ...], tmp_path: Path) -> None:
        text = (
            "The quick brown fox jumps over the lazy dog.\n"
            "The dog barked at the fox.\n"
            "The fox ran away.\n"
        )
        result = _run(submission_command, text, tmp_path)
        assert result["lines"] == 3
        assert result["characters"] == len(text)
        assert result["words"] == 19
        # "the" appears 5 times (case-insensitive)
        top_word = result["top_words"][0]
        assert top_word["word"] == "the"
        assert top_word["count"] == 5
