For technical compatibility, please implement this in Python 3.11+. Use only the Python standard library — do not use any external or third-party dependencies. The tool should be a single-file program runnable as:

```
python main.py --input <input_file> --output <output_file>
```

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
- 1: input was malformed or could not be read
- 2: internal error

Place all source files in the `output/` directory relative to your current working directory. The entry point must be `output/main.py`.
