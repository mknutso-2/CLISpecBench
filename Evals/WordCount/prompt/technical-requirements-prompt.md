For technical compatibility, please implement this in C++20, buildable with cmake. Use only the C++ standard library — do not use any external or third-party dependencies. The tool should accept these command-line flags:

```
<executable> --input <input_file> --output <output_file>
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

Place all source files (including `CMakeLists.txt`) in the `output/` directory relative to your current working directory.
