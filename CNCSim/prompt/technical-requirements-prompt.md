- Please implement this in C++20, buildable with: cmake -B build && cmake --build build
- The program must accept: --input <gcode_file> --output <result_file>
- The harness may also pass: --tool-table <tool_file>
  If provided, this file uses the RS274 tool-file format from section 2.3 of the specification.
- The harness may also pass: --carousel-slots <slot_count>
  If provided, this is the number of slots in the carousel/tool changer.
- The harness may also pass: --parameter-input <parameter_file> and/or
  --parameter-output <parameter_file>
  If provided, these files use the RS274 parameter-file format from section 3.2.1 of the
  specification.
  If --parameter-output is provided and execution succeeds, write a parameter file at that path.
  For the written file, follow the RS274 section 3.2.1 rules and include any additional parameters
  that were loaded from --parameter-input or set during execution.
- The harness may also pass: --probe-box <x_min> <x_max> <y_min> <y_max> <z_min> <z_max>
  and/or --probe-tool <tool_number>
  If provided, --probe-box defines an axis-aligned probeable box in absolute machine coordinates,
  with all six numeric extents expressed in inches. For G38.2 in this task, a probe trip occurs
  when the RS274 controlled point first enters that box; no additional probe-tip length, radius,
  or stylus shape is modeled. If provided, --probe-tool gives the tool number that should be
  treated as a probe for G38.2.
- The output file must be JSON in this format:
  {
    "machine_position": {"x": float, "y": float, "z": float, "a": float, "b": float, "c": float},
    "feed_rate": float,
    "spindle_speed": float,
    "spindle_direction": "CW" | "CCW" | "OFF",
    "cutter_radius_compensation_number": integer | null,
    "tool_length_offset_index": integer | null,
    "selected_tool": integer | null,
    "tool_in_spindle": integer | null,
    "active_modal_g_codes": {"<group_number>": string, ...},
    "active_modal_m_codes": {"<group_number>": string, ...},
    "coordinate_system_offsets": {
      "<system_number>": {
        "x": float, "y": float, "z": float, "a": float, "b": float, "c": float
      },
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
  Serialize rotary axes A, B, and C in degrees, without G20/G21 unit conversion or modulo
  normalization.
  Serialize "cutter_radius_compensation_number" as the active D number, or null if no explicit
  cutter radius compensation number is active.
  Serialize "tool_length_offset_index" as the active H number, or null if no tool length offset
  index is active.
  Serialize "selected_tool" as the currently selected T number, or null if no tool has been
  selected.
  Serialize "tool_in_spindle" as the tool currently loaded in the spindle after any completed M6,
  or null if the spindle is empty.
  Serialize "active_modal_g_codes" as a JSON object whose keys are RS274 modal group numbers
  encoded as JSON strings and whose values are G-code strings (for example:
  {"1": "G1", "3": "G90"}).
  Serialize "active_modal_m_codes" as a JSON object whose keys are RS274 M-code modal group
  numbers encoded as JSON strings and whose values are M-code strings (for example:
  {"7": "M5"}).
  Serialize "coordinate_system_offsets" as a JSON object whose keys are program coordinate
  system numbers 1 through 9 encoded as JSON strings and whose values are objects of the form
  {"x": float, "y": float, "z": float, "a": float, "b": float, "c": float}.
  Serialize "parameters" as a JSON object whose keys are RS274 parameter numbers encoded as
  JSON strings and whose values are the corresponding numeric parameter values.
  This object may be sparse. Omitted parameter numbers mean the simulator is not reporting a
  value for that parameter in the payload. Any included parameter number must have a numeric
  value.
- Exit 0 on success. If the input program triggers any error condition documented in the
  specification document, treat that as invalid input and exit 1. Use exit 2 only for internal
  errors in the simulator itself rather than spec-defined program errors.
