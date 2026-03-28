- Please implement this in C++20, buildable with: cmake -B build && cmake --build build
- The program must accept: --input <gcode_file> --output <result_file>
- The output file must be JSON in this format:
  {
    "final_position": {"x": float, "y": float, "z": float},
    "feed_rate": float,
    "spindle_speed": float,
    "spindle_direction": "CW" | "CCW" | "OFF",
    "active_modal_g_codes": {"<group_number>": string, ...},
    "active_modal_m_codes": {"<group_number>": string, ...},
    "coordinate_system_offsets": {
      "<system_number>": {"x": float, "y": float, "z": float},
      ...
    },
    "error": string | null
  }
  Serialize "active_modal_g_codes" as a JSON object whose keys are RS274 modal group numbers
  encoded as JSON strings and whose values are G-code strings (for example:
  {"1": "G1", "3": "G90"}).
  Serialize "active_modal_m_codes" as a JSON object whose keys are RS274 M-code modal group
  numbers encoded as JSON strings and whose values are M-code strings (for example:
  {"7": "M5"}).
  Serialize "coordinate_system_offsets" as a JSON object whose keys are program coordinate
  system numbers 1 through 9 encoded as JSON strings and whose values are objects of the form
  {"x": float, "y": float, "z": float}.
- Exit 0 on success, 1 for invalid input, 2 for internal errors
