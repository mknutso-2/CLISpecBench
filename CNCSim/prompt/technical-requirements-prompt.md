- Please implement this in C++20, buildable with: cmake -B build && cmake --build build
- The program must accept: --input <gcode_file> --output <result_file>
- The harness may also pass: --tool-table <tool_file>
  If provided, this file uses the RS274 tool-file format from section 2.3 of the specification.
- The harness may also pass: --parameter-input <parameter_file> and/or
  --parameter-output <parameter_file>
  If provided, these files use the RS274 parameter-file format from section 3.2.1 of the
  specification.
  If --parameter-output is provided and execution succeeds, write a parameter file at that path.
  For the written file, follow the RS274 section 3.2.1 rules and include any additional parameters
  that were loaded from --parameter-input or set during execution.
- The output file must be JSON in this format:
  {
    "machine_position": {"x": float, "y": float, "z": float},
    "feed_rate": float,
    "spindle_speed": float,
    "spindle_direction": "CW" | "CCW" | "OFF",
    "cutter_radius_compensation_number": integer | null,
    "tool_length_offset_index": integer | null,
    "selected_tool": integer | null,
    "active_modal_g_codes": {"<group_number>": string, ...},
    "active_modal_m_codes": {"<group_number>": string, ...},
    "coordinate_system_offsets": {
      "<system_number>": {"x": float, "y": float, "z": float},
      ...
    },
    "parameters": {"<parameter_number>": float, ...},
    "error": string | null
  }
  Write this JSON file on both success and error. On success, "error" must be null. On invalid
  input or internal failure, "error" must be a non-empty string.
  Serialize "machine_position" as the absolute machine-coordinate position of the RS274
  controlled point (the coordinate space used by G53), after applying any active tool length
  compensation.
  Serialize "machine_position" and "coordinate_system_offsets" in the currently active RS274
  length units at end of program.
  Serialize "cutter_radius_compensation_number" as the active D number, or null if no explicit
  cutter radius compensation number is active.
  Serialize "tool_length_offset_index" as the active H number, or null if no tool length offset
  index is active.
  Serialize "selected_tool" as the currently selected T number, or null if no tool has been
  selected.
  Serialize "active_modal_g_codes" as a JSON object whose keys are RS274 modal group numbers
  encoded as JSON strings and whose values are G-code strings (for example:
  {"1": "G1", "3": "G90"}).
  Serialize "active_modal_m_codes" as a JSON object whose keys are RS274 M-code modal group
  numbers encoded as JSON strings and whose values are M-code strings (for example:
  {"7": "M5"}).
  Serialize "coordinate_system_offsets" as a JSON object whose keys are program coordinate
  system numbers 1 through 9 encoded as JSON strings and whose values are objects of the form
  {"x": float, "y": float, "z": float}.
  Serialize "parameters" as a JSON object whose keys are RS274 parameter numbers encoded as
  JSON strings and whose values are the corresponding numeric parameter values.
  This object may be sparse. Omitted parameter numbers mean the simulator is not reporting a
  value for that parameter in the payload. Any included parameter number must have a numeric
  value.
- Exit 0 on success. If the input program triggers any error condition documented in the
  specification document, treat that as invalid input and exit 1. Use exit 2 only for internal
  errors in the simulator itself rather than spec-defined program errors.
