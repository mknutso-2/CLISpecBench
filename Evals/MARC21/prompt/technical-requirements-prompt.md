The program must be runnable as:

```text
python main.py --input <request.json> --output <response.json>
```

The program must be self-contained: only files placed in `output/` will be
present at run time. Any reference data the program needs at run time (rule
tables, lookup files, embedded constants, etc.) must live inside `output/` —
files anywhere else in the project tree (including `docs/`) are not available
when the program runs.

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

The MARCXML input may also be a MARC21 slim `<collection>` element containing
exactly one `<record>` child.

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

The canonical JSON `record` shape always uses `leader_template` as a normalized
24-character leader template. On successful `inspect` and `inspect_marcxml`
results, positions `00-04` and `12-16` must be returned as `00000` in
`leader_template` even though the source ISO 2709 record or MARCXML leader
contains concrete length and base-address digits. `render_iso2709` must fill
those positions back in from the actual serialized ISO 2709 record length and
base address. `render_marcxml` must emit the normalized leader template because
MARCXML has no ISO 2709 directory or base-address serialization.

The ISO 2709 interchange scope for this eval is Unicode text encoded as
UTF-8; MARC-8 conversion is out of scope even when Leader/09 uses the blank
code permitted by the MARC 21 leader documentation. The `base-prompt.md` and
`docs/` files describe the UTF-8 and MARC validation behavior; the
`invalid_record` error code below is the one reported when that validation
rejects an `inspect` or `inspect_marcxml` input.

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
