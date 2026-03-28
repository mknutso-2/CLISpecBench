- Please implement this in C++20, buildable with: cmake -B build && cmake --build build
- The program must accept: --input <gcode_file> --output <result_file>
- The output file must be JSON in this format:
  {
    "final_position": {"x": float, "y": float, "z": float},
    "feed_rate": float,
    "spindle_speed": float,
    "spindle_direction": "CW" | "CCW" | "OFF",
    "active_modal_codes": {"<group_number>": string, ...},
    "error": string | null
  }
  Keys in "active_modal_codes" must be RS274 modal group numbers encoded as JSON strings
  (for example: {"1": "G1", "3": "G90"}).
- Exit 0 on success, 1 for invalid input, 2 for internal errors
