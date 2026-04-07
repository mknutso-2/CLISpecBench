The tool must accept these command-line flags:

`--input`: path to the plain-text file to analyze.
`--output`: path where the tool should write its JSON result.

The output file must be a JSON object in this format:

```json
{
  "lines": integer,
  "words": integer,
  "characters": integer,
  "unique_words": integer,
  "top_words": [
    {"word": string, "count": integer},
    ...
  ]
}
```

Exit codes:
- 0: completed successfully, output written
- 1: invocation was invalid — required arguments missing, unknown arguments,
  or the input file was missing, unreadable, or malformed
- 2: unexpected internal error (e.g. panic, out-of-memory)
