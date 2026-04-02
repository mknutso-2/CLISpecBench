# WordCount Specification

## Overview

WordCount is a command-line text analysis tool. Given a plain-text input file, it produces a JSON report containing basic text statistics and word frequency data.

## Definitions

- **Line**: A sequence of zero or more characters terminated by a newline character (`\n`). The last line in a file need not end with a newline. An empty file has zero lines.
- **Character**: Every byte in the file counts as one character, including newline characters.
- **Word**: A maximal contiguous sequence of non-whitespace characters. Whitespace characters are: space (` `), tab (`\t`), newline (`\n`), carriage return (`\r`), form feed (`\f`), and vertical tab (`\v`). Words are compared case-insensitively for frequency counting (convert to lowercase). A file with only whitespace has zero words.

## Output

The tool produces a JSON object with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `lines` | integer | Number of lines in the input |
| `words` | integer | Total number of words |
| `characters` | integer | Total number of characters (bytes) |
| `unique_words` | integer | Number of distinct words (case-insensitive) |
| `top_words` | array | The 10 most frequent words, or all words if fewer than 10 exist |

Each entry in `top_words` is an object:

| Field | Type | Description |
|-------|------|-------------|
| `word` | string | The word in lowercase |
| `count` | integer | Number of occurrences |

### Ordering of `top_words`

1. Primary sort: descending by `count`.
2. Tie-breaker: ascending alphabetical order (standard lexicographic comparison on the lowercase form).

If the file contains no words, `top_words` is an empty array.

## Edge Cases

- **Empty file**: `lines` = 0, `words` = 0, `characters` = 0, `unique_words` = 0, `top_words` = [].
- **File with only whitespace**: `words` = 0, `unique_words` = 0, `top_words` = []. Lines and characters are counted normally.
- **No trailing newline**: A file containing `hello` (5 bytes, no newline) has 1 line, 1 word, 5 characters.
- **Trailing newline**: A file containing `hello\n` (6 bytes) has 1 line, 1 word, 6 characters.
- **Multiple consecutive newlines**: Each `\n` terminates a line. `\n\n\n` is 3 lines.
- **Case insensitivity**: `Hello`, `HELLO`, and `hello` are the same word for frequency counting. They all appear as `hello` in `top_words`.
- **Punctuation**: Punctuation attached to a word is part of the word. `hello,` and `hello` are different words.
