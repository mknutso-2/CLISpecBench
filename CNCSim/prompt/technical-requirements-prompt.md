- Please implement this in C++20, buildable with: cmake -B build && cmake --build build
- The program must accept: --input <gcode_file> --output <result_file>
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
    "error": string | null
  }
  Write this JSON file on both success and error. On success, "error" must be null. On invalid
  input or internal failure, "error" must be a non-empty string.
  Serialize "machine_position" as the tool position in the absolute machine coordinate system
  (the coordinate space used by G53).
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
- Exit 0 on success. If the input program triggers any error condition documented in the
  specification document, treat that as invalid input and exit 1. Use exit 2 only for internal
  errors in the simulator itself rather than spec-defined program errors.
