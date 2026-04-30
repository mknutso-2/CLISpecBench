The program must accept these command-line flags:

- `--input <path>`: path to a JSON file containing the request.
- `--output <path>`: path where the program writes its JSON response.

## Request schema

The input file is always a JSON object with an `action` field.

### `inspect`

```json
{
  "action": "inspect",
  "las_b64": "TEFTRgAAAAAA..."
}
```

`las_b64` is a base64-encoded LAS file.

### `render`

```json
{
  "action": "render",
  "dataset": {
    "header": {
      "file_source_id": 7,
      "global_encoding": 16,
      "project_id": "123e4567-e89b-12d3-a456-426614174000",
      "version_major": 1,
      "version_minor": 4,
      "system_identifier": "MERGE",
      "generating_software": "Example 1.0",
      "file_creation_day_of_year": 42,
      "file_creation_year": 2026,
      "point_data_record_format": 6,
      "x_scale_factor": 0.01,
      "y_scale_factor": 0.01,
      "z_scale_factor": 0.01,
      "x_offset": 0.0,
      "y_offset": 0.0,
      "z_offset": 0.0
    },
    "vlrs": [
      {
        "user_id": "LASF_Projection",
        "record_id": 2112,
        "description": "WKT CRS",
        "kind": "wkt_coordinate_system",
        "text": "GEOGCS[\"WGS 84\"]"
      }
    ],
    "points": [
      {
        "x": 100,
        "y": 200,
        "z": 300,
        "intensity": 5,
        "return_number": 1,
        "number_of_returns": 1,
        "scan_direction_flag": false,
        "edge_of_flight_line": false,
        "classification": 2,
        "synthetic": false,
        "key_point": false,
        "withheld": false,
        "overlap": false,
        "scanner_channel": 0,
        "user_data": 0,
        "scan_angle": 0,
        "point_source_id": 7,
        "gps_time": 1000.0
      }
    ],
    "evlrs": []
  }
}
```

## Dataset schema

The dataset is a JSON object with:

- `header`: LAS public-header fields
- `vlrs`: ordered list of VLR objects
- `points`: ordered list of point-record objects
- `evlrs`: ordered list of EVLR objects

### Header object

Required semantic fields:

- `file_source_id`: integer
- `global_encoding`: integer
- `project_id`: canonical UUID string
- `version_major`: integer
- `version_minor`: integer
- `system_identifier`: string
- `generating_software`: string
- `file_creation_day_of_year`: integer
- `file_creation_year`: integer
- `point_data_record_format`: integer 0 through 10
- `x_scale_factor`, `y_scale_factor`, `z_scale_factor`: numbers
- `x_offset`, `y_offset`, `z_offset`: numbers

Inspect results include the public-header fields below exactly as stored in the
LAS file. Render requests may include these fields, but the renderer must
recompute them from the semantic content instead of trusting the supplied
values:

- `header_size`
- `offset_to_point_data`
- `number_of_variable_length_records`
- `point_data_record_length`
- `legacy_number_of_point_records`
- `legacy_number_of_points_by_return`
- `max_x`, `min_x`, `max_y`, `min_y`, `max_z`, `min_z`
- `start_of_waveform_data_packet_record`
- `start_of_first_extended_variable_length_record`
- `number_of_extended_variable_length_records`
- `number_of_point_records`
- `number_of_points_by_return`

`legacy_number_of_points_by_return` must be a 5-element array when present.
`number_of_points_by_return` must be a 15-element array when present.

### Point objects

Every point object includes:

- `x`, `y`, `z`: signed integers
- `intensity`: integer
- `return_number`: integer
- `number_of_returns`: integer
- `scan_direction_flag`: boolean
- `edge_of_flight_line`: boolean
- `classification`: integer
- `user_data`: integer
- `point_source_id`: integer

For point formats 0 through 5:

- `scan_angle_rank`: integer
- `synthetic`, `key_point`, `withheld`: booleans

For point formats 1, 3, 4, and 5:

- `gps_time`: number

For point formats 2, 3, 5, 7, 8, and 10:

- `color`: object with `red`, `green`, and `blue` integer fields

For point formats 4, 5, 9, and 10:

- `waveform`: object with:
  - `descriptor_index`
  - `byte_offset_to_waveform_data`
  - `waveform_packet_size_in_bytes`
  - `return_point_waveform_location`
  - `xt`
  - `yt`
  - `zt`

When serializing a point in formats 4, 5, 9, or 10 that omits the optional
`waveform` object, write descriptor index 0 followed by zero-valued waveform
fields into the corresponding point-record bytes.

For point formats 6 through 10:

- `synthetic`, `key_point`, `withheld`, `overlap`: booleans
- `scanner_channel`: integer
- `scan_angle`: integer
- `gps_time`: number

For point formats 8 and 10:

- `nir`: integer

If the point record length is larger than the minimum size for the selected
point format, expose the remaining bytes as:

- `extra_bytes_b64`: base64 string

### VLR and EVLR objects

Every VLR/EVLR object includes:

- `user_id`: string
- `record_id`: integer
- `description`: string
- `kind`: string

Supported `kind` values and payload fields:

- `opaque`
  - `data_b64`
- `classification_lookup`
  - `entries`: array of objects with `class_number` and `description`
  - omitted class numbers are treated as empty descriptions on render
- `text_area_description`
  - `text`
- `wkt_math_transform`
  - `text`
- `wkt_coordinate_system`
  - `text`
- `geo_key_directory`
  - `key_directory_version`
  - `key_revision`
  - `minor_revision`
  - `keys`: array of objects with `key_id`, `tiff_tag_location`, `count`,
    `value_offset`
- `geo_double_params`
  - `values`: array of numbers
- `geo_ascii_params`
  - `text`
- `extra_bytes`
  - `descriptors`: array of objects with:
    - `data_type`
    - `options`
    - `name`
    - `description`
    - `no_data`
    - `min`
    - `max`
    - `scale`
    - `offset`
  - `no_data`, `min`, `max`, `scale`, and `offset` are always 3-element arrays
- `waveform_packet_descriptor`
  - `bits_per_sample`
  - `waveform_compression_type`
  - `number_of_samples`
  - `temporal_sample_spacing`
  - `digitizer_gain`
  - `digitizer_offset`
- `waveform_data_packets`
  - `data_b64`
  - The waveform packet payload bytes are surfaced opaquely. Intra-packet
    structure (per-packet sample layout, per-packet padding to even byte
    boundaries when bits-per-sample is not a multiple of 8) is not validated
    by inspect or render and the bytes round-trip unchanged.
- `superseded`
  - `data_b64`
  - LASF_Spec / 7 marker used to negate a previously-written VLR or EVLR.
    Treated as a tagged opaque payload: `data_b64` round-trips unchanged.

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
    "offset": 1234
  },
  "result": null
}
```

`offset` is optional and should be omitted when there is no relevant byte
offset.

Allowed `error.code` values:

- `invalid_request`: malformed request JSON, unsupported action, or invalid
  render dataset
- `invalid_document`: an inspected LAS file violates the LAS 1.4 docs corpus
- `internal_error`: unexpected internal failure

## Successful result payloads

### `inspect`

```json
{
  "status": "ok",
  "error": null,
  "result": {
    "dataset": {
      "header": {
        "file_source_id": 7,
        "global_encoding": 16,
        "project_id": "123e4567-e89b-12d3-a456-426614174000",
        "version_major": 1,
        "version_minor": 4,
        "system_identifier": "MERGE",
        "generating_software": "Example 1.0",
        "file_creation_day_of_year": 42,
        "file_creation_year": 2026,
        "header_size": 375,
        "offset_to_point_data": 446,
        "number_of_variable_length_records": 1,
        "point_data_record_format": 6,
        "point_data_record_length": 30,
        "legacy_number_of_point_records": 0,
        "legacy_number_of_points_by_return": [0, 0, 0, 0, 0],
        "x_scale_factor": 0.01,
        "y_scale_factor": 0.01,
        "z_scale_factor": 0.01,
        "x_offset": 0.0,
        "y_offset": 0.0,
        "z_offset": 0.0,
        "max_x": 1.0,
        "min_x": 1.0,
        "max_y": 2.0,
        "min_y": 2.0,
        "max_z": 3.0,
        "min_z": 3.0,
        "start_of_waveform_data_packet_record": 0,
        "start_of_first_extended_variable_length_record": 0,
        "number_of_extended_variable_length_records": 0,
        "number_of_point_records": 1,
        "number_of_points_by_return": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
      },
      "vlrs": [
        {
          "user_id": "LASF_Projection",
          "record_id": 2112,
          "description": "WKT CRS",
          "kind": "wkt_coordinate_system",
          "text": "GEOGCS[\"WGS 84\"]"
        }
      ],
      "points": [
        {
          "x": 100,
          "y": 200,
          "z": 300,
          "intensity": 5,
          "return_number": 1,
          "number_of_returns": 1,
          "scan_direction_flag": false,
          "edge_of_flight_line": false,
          "classification": 2,
          "synthetic": false,
          "key_point": false,
          "withheld": false,
          "overlap": false,
          "scanner_channel": 0,
          "user_data": 0,
          "scan_angle": 0,
          "point_source_id": 7,
          "gps_time": 1000.0
        }
      ],
      "evlrs": []
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
    "las_b64": "TEFTRgAAAAAA..."
  }
}
```

## Exit codes

- `0`: completed successfully, output written
- `1`: invalid invocation, malformed request JSON, or a document/render error
- `2`: unexpected internal error
