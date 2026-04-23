The program must be runnable as:

```text
python main.py --input <request.json> --output <response.json>
```

## Request schema

The input file is always a JSON object with an `action` field.

### `inspect`

```json
{
  "action": "inspect",
  "gedcom_text": "0 HEAD\n1 GEDC\n2 VERS 7.0\n0 TRLR\n"
}
```

### `render`

```json
{
  "action": "render",
  "dataset": {
    "records": [
      {
        "tag": "HEAD",
        "xref": null,
        "payload": null,
        "children": [
          {
            "tag": "GEDC",
            "xref": null,
            "payload": null,
            "children": [
              {
                "tag": "VERS",
                "xref": null,
                "payload": "7.0",
                "children": []
              }
            ]
          }
        ]
      },
      {
        "tag": "TRLR",
        "xref": null,
        "payload": null,
        "children": []
      }
    ]
  }
}
```

Each record or nested structure is represented as an object with:

- `tag`: string GEDCOM tag
- `xref`: string or `null`
- `payload`: string or `null`
- `children`: ordered list of nested structures

If a GEDCOM payload uses `CONT` continuation lines, represent the embedded line
breaks inside the parent structure's `payload` string. Do not surface `CONT` as
an ordinary child node in the JSON tree.

## Response schema

The output file must always be a JSON object with this top-level shape:

```json
{
  "status": "ok",
  "error": null,
  "result": {}
}
```

On failure:

```json
{
  "status": "error",
  "error": {
    "code": "invalid_document",
    "message": "Human-readable explanation",
    "line": 7
  },
  "result": null
}
```

`line` is optional and should be omitted when no specific line applies.

The allowed `error.code` values are:

- `invalid_request`: malformed request JSON, unsupported action, or invalid
  dataset supplied to `render`
- `invalid_document`: `inspect` input violates the GEDCOM specification corpus
  in `docs/`
- `internal_error`: unexpected internal failure

## Successful result payloads

### `inspect`

```json
{
  "status": "ok",
  "error": null,
  "result": {
    "dataset": {
      "records": [
        {
          "tag": "HEAD",
          "xref": null,
          "payload": null,
          "children": [
            {
              "tag": "GEDC",
              "xref": null,
              "payload": null,
              "children": [
                {
                  "tag": "VERS",
                  "xref": null,
                  "payload": "7.0",
                  "children": []
                }
              ]
            }
          ]
        },
        {
          "tag": "TRLR",
          "xref": null,
          "payload": null,
          "children": []
        }
      ]
    }
  }
}
```

### `render`

```json
{
  "status": "ok",
  "error": null,
  "result": {
    "gedcom_text": "0 HEAD\n1 GEDC\n2 VERS 7.0\n0 TRLR\n"
  }
}
```

## Exit codes

- `0`: completed successfully, output written
- `1`: invalid invocation, malformed request JSON, or a document/render error
- `2`: unexpected internal error
