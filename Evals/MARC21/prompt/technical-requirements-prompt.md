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
  "record_b64": "base64-encoded ISO2709 bytes"
}
```

### `inspect_marcxml`

```json
{
  "action": "inspect_marcxml",
  "marcxml": "<record xmlns=\"http://www.loc.gov/MARC21/slim\">...</record>"
}
```

### `render_iso2709`

```json
{
  "action": "render_iso2709",
  "record": {
    "leader_template": "00000nam a2200000 a 4500",
    "control_fields": [],
    "data_fields": []
  }
}
```

### `render_marcxml`

```json
{
  "action": "render_marcxml",
  "record": {
    "leader_template": "00000nam a2200000 a 4500",
    "control_fields": [],
    "data_fields": []
  }
}
```

## Response schema

The output file must always be a JSON object with top-level fields:

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
    "code": "invalid_record",
    "message": "Human-readable explanation"
  },
  "result": null
}
```

Allowed `error.code` values:

- `invalid_request`
- `invalid_record`
- `internal_error`

Use them as follows:

- `invalid_request`: malformed request JSON, unsupported action, or invalid
  canonical record supplied to a render action
- `invalid_record`: `inspect` or `inspect_marcxml` input violates the MARC 21
  bibliographic specification corpus in `docs/`
- `internal_error`: unexpected internal failure

## Successful result payloads

### `inspect` and `inspect_marcxml`

```json
{
  "status": "ok",
  "error": null,
  "result": {
    "record": {
      "leader_template": "00000nam a2200000 a 4500",
      "control_fields": [
        {"tag": "001", "value": "12345"}
      ],
      "data_fields": [
        {
          "tag": "245",
          "indicators": ["1", "0"],
          "subfields": [
            {"code": "a", "value": "Example title :"},
            {"code": "c", "value": "Example author."}
          ]
        }
      ]
    }
  }
}
```

### `render_iso2709`

```json
{
  "status": "ok",
  "error": null,
  "result": {
    "record_b64": "base64-encoded ISO2709 bytes"
  }
}
```

### `render_marcxml`

```json
{
  "status": "ok",
  "error": null,
  "result": {
    "marcxml": "<record xmlns=\"http://www.loc.gov/MARC21/slim\">...</record>"
  }
}
```

## Exit codes

- `0`: completed successfully, output written
- `1`: invalid invocation, malformed request, or record/profile error
- `2`: unexpected internal error
