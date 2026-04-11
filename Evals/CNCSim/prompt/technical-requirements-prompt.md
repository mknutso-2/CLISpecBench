- The program must accept: --input <gcode_file> --output <result_file>
- The harness may also pass: --tool-table <tool_file>
  If provided, this file uses the RS274 tool-file format from section 2.3 of the specification.
- The harness may also pass: --block-delete
  If provided, treat slash-prefixed blocks as skipped, as if the RS274 block-delete switch were ON.
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
- The harness may also pass: --trace-output <trace_file>
  If provided, write a motion trace JSON file at this path on both success and error. The trace
  file is independent of --output; both files are written in the same run.
- Whenever --trace-output is provided, exactly one of --trace-time-step, --trace-distance-step,
  or --trace-position-tolerance must also be provided. Providing zero, providing more than one,
  or providing any of them without --trace-output is invalid input (exit 1).
  --trace-time-step <seconds>
    Positive float, in seconds. Sample trace entries at fixed time intervals of the given step
    within each moving line.
  --trace-distance-step <inches>
    Positive float, in inches (independent of active G20/G21 mode). Sample trace entries at
    fixed Euclidean path-distance intervals within each moving line.
  --trace-position-tolerance <inches>
    Positive float, in inches (independent of active G20/G21 mode). Sample trace entries
    adaptively so that linear interpolation of "machine_position" between any two consecutive
    entries deviates from the true path by at most this tolerance.
- The trace file must be JSON in this format:
  {
    "initial_state": { ... },
    "entries": [ ... ],
    "error_line_number": integer | null,
    "error_block_segment_index": integer | null
  }
  Write this file on both success and error. On success, both "error_line_number" and
  "error_block_segment_index" must be null. On error, "error_line_number" must be the 1-based
  source line of the failing block, and "error_block_segment_index" must be the 0-based index
  of the failing sub-motion within a multi-sub-motion expansion (e.g., the failing peck of a
  G83 drill), or null if the failing block had only a single sub-motion.
- "initial_state" is a full, non-sparse snapshot of machine state taken immediately before the
  first block of the program executes, after --parameter-input and --tool-table have been
  applied. Its shape matches the --output payload exactly, except that the "error" field is
  omitted.
- "entries" is a JSON array of delta state objects in execution order. Each entry is a JSON
  object using the same field names and serialization rules as the --output payload, with these
  differences:
  - "error" must not be included.
  - Every field inherited from --output is optional; if a field is present, it must not be
    null, with one exception: the four nullable scalar fields
    "cutter_radius_compensation_number", "tool_length_offset_index", "selected_tool", and
    "tool_in_spindle" may appear with the explicit value null to encode a transition from a
    non-null prior value to null (for example, the reset performed by M2 or M30, which turns
    cutter radius compensation off). These four fields still follow the delta rule: include
    the field if and only if its value differs from the prior entry, and if it does differ,
    write its new value verbatim (including null when the new value is null).
  - "machine_position" includes only the axes whose values differ from the prior entry (or
    from "initial_state" for the first entry in "entries").
  - "coordinate_system_offsets" includes only the coordinate systems (top-level keys "1"
    through "9") whose per-system offsets have changed since the prior entry; coordinate
    systems whose offsets are unchanged are omitted from the entry entirely. Each included
    per-system object itself includes only the axes whose values differ.
  - "active_modal_g_codes" and "active_modal_m_codes" include only the modal group numbers
    whose values differ.
  - "parameters" includes only the parameter numbers whose values differ.
  - The scalar fields "feed_rate", "spindle_speed", "spindle_direction",
    "cutter_radius_compensation_number", "tool_length_offset_index", "selected_tool", and
    "tool_in_spindle" are included only if the value differs from the prior entry. There is no
    per-source-line cap on how often these may change; the tapping cycles G84 and G74
    legitimately flip "spindle_direction" twice on a single source line.
  - Coordinates in entries ("machine_position" and "coordinate_system_offsets") are absolute
    machine coordinates (G53 space), after any active tool length compensation and any active
    G92 offset. Lengths use the currently active G20/G21 units at the moment the entry is
    emitted. When cutter radius compensation is active, "machine_position" describes the
    compensated (tool-tip) path.
- Each entry also adds these fields:
  - "line_number": integer, the 1-based source line of the input G-code block that induced the
    entry. For blocks that expand into multiple sub-motions (canned cycles, G28/G30,
    cutter-comp lead-in/lead-out), every resulting entry carries the source line of the
    originating block.
  - "time": float, seconds elapsed since the start of execution of the source line identified
    by "line_number". Always in seconds, independent of G93/G94/G95. Cumulative within the
    source line: it is the sub-motion's start time (measured from the start of the line) plus
    the sub-motion-local sample time, and is not reset at sub-motion boundaries. No entry is
    emitted at "time" == 0.0 on a motion line; modal, parameter, tool, coordinate-system, and
    label deltas that would otherwise have ridden a "time" == 0.0 entry ride the line's first
    emitted entry instead (see the stepping rules below). The final entry of a motion line
    has "time" equal to the line's total duration (the sum of all sub-motion durations on
    that line).
  - "motion_kind": optional string, one of "rapid" or "feed". Present only on the first
    emitted entry of each sub-motion inside a canned cycle expansion (G81, G82, G83, G84, G74,
    G85, G86, G87, G88, G89). The "first emitted entry of a sub-motion" is the earliest entry
    whose cumulative "time" falls within that sub-motion's extent -- the first interior
    stepped sample if any exist, otherwise the sub-motion's final entry. Omitted on subsequent
    stepped samples within the same sub-motion, on final entries that are not the sub-motion's
    first emitted entry, and everywhere outside canned cycles.
  - "nonmodal_g_codes": optional array of strings. The RS274 group-0 non-modal G-codes
    executed by the originating block. Order within the array is alphabetical. The field is
    omitted entirely -- not null, not [] -- when no non-modal fired on the originating block.
    G92, G92.1, G92.2, and G92.3 must appear as the exact strings "G92", "G92.1", "G92.2",
    "G92.3". The field is attached as follows depending on the block kind:
      - For a block that produces at least one sub-motion (e.g., G53 applied to a G1 move,
        or G28/G30 which expand into two sub-motions), the label is attached to the first
        emitted entry of each sub-motion induced by the non-modal. Stepped samples that are
        not the sub-motion's first emitted entry do not re-emit it. G28 and G30 each expand
        into two sub-motions (move to intermediate point, then move to the parameterized
        destination); the label appears on the first emitted entry of each sub-motion that
        produces any entries. A zero-duration sub-motion (e.g., a G28 whose block specifies
        no intermediate axis words, so the intermediate point equals the current position)
        produces no entries, and the label associated with such a sub-motion is not rolled
        forward to a subsequent sub-motion.
      - For a block that produces no sub-motion because the non-modal itself is state-only
        (G10, G92, G92.1, G92.2, G92.3), the label is attached to the block's sole
        "time" == 0.0001 state-only entry.
      - For a G4 dwell block, the label is attached to the block's sole dwell entry at
        "time" == P.
- Time in trace entries is computed assuming instantaneous linear and angular acceleration.
  - Feed motion (G1, G2, G3, canned-cycle feed moves, threading, G38.2 probing): duration
    equals true path length divided by the effective feed rate. Path length is Euclidean for
    linear motion and true arc length for G2/G3, including the axial component for helical
    arcs. A center-format arc whose programmed start and end points coincide is a full circle
    of path length 2*pi*radius (not zero). Effective feed rate follows the active feed-rate
    mode (G93 inverse-time, G94 units/min, G95 units/rev). Under G93 inverse-time, the
    moving block's total duration is 1/F seconds regardless of geometry; on a block that
    expands into multiple feed sub-motions, each sub-motion's duration is 1/F apportioned in
    proportion to its path length so that the sub-motion durations sum to 1/F.
  - Rapid motion (G0 and canned-cycle rapid sub-motions): duration is computed at a fixed rate
    of 1000 inches/minute. Path length is converted to inches before division.
  - Dwell (G4 with P > 0): exactly one entry with "time" equal to the P value converted to
    seconds per the active feed-rate mode's time convention. The entry carries
    "nonmodal_g_codes": ["G4"] plus any other state deltas produced on the same block.
  - State-only blocks (modal changes, parameter assignments, tool selection without motion,
    and similar blocks that change state without producing motion, including M2/M30
    program-end which resets cutter compensation, origin offsets, and spindle state):
    exactly one entry with "time" == 0.0001 carrying the full delta of every state change
    produced by the block. Any parameter writes performed as an implicit side effect of
    the block (including M2/M30's implicit parameter resets) are reported in the
    "parameters" delta on the same entry.
  - Blocks that produce no observable state change (comments, block-deleted lines when
    --block-delete is active, pure O-word control flow, G4 with P == 0): no entry is emitted,
    and the source line does not appear in "entries".
- Stepping is applied independently per sub-motion. A line with no sub-motion structure
  (ordinary G0/G1/G2/G3/G38.2 motion, including a cutter-compensated straight or arc move
  whose lead-in or lead-out is geometrically part of the same single tool-tip path) is
  treated as having exactly one sub-motion whose duration and path length equal the line's
  total duration and path length. A line that expands into multiple sub-motions (canned
  cycles, G28, G30) applies the stepping rule to each sub-motion separately.
- Stepping mode semantics (applied within each sub-motion of duration L_time seconds and
  path length L_dist inches):
  - --trace-time-step dt: emit interior samples at sub-motion-local times dt, 2*dt, ...
    strictly less than L_time, plus a sub-motion final entry at sub-motion-local time
    L_time. No entry is emitted at sub-motion-local time 0.
  - --trace-distance-step ds: emit interior samples at sub-motion-local cumulative path
    distances ds, 2*ds, ... strictly less than L_dist, plus a sub-motion final entry at
    sub-motion-local distance L_dist. No entry is emitted at sub-motion-local distance 0.
  - --trace-position-tolerance eps: emit samples adaptively such that linear interpolation
    of "machine_position" between any two consecutive entries within the sub-motion deviates
    from the true (possibly curved) path by at most eps inches at all intermediate points.
    No entry is emitted at sub-motion-local time 0.
- Every non-zero sub-motion has a final entry at its sub-motion-local time L_time, always
  emitted.
- Zero-duration, zero-path-length sub-motions (e.g., a canned cycle whose rapid-to-XY target
  equals the current XY, or a G28 whose block specifies no intermediate axis words) produce
  no entries. Any motion_kind or nonmodal_g_codes label associated with such a sub-motion is
  not rolled forward to any other sub-motion; the label simply does not appear in the trace.
- The line's first emitted entry is the first interior stepped sample of its first non-zero
  sub-motion, or that sub-motion's final entry if no interior sample fits inside it. Any
  modal, parameter, tool, coordinate-system, and label deltas that would otherwise have
  ridden a "time" == 0.0 entry ride the line's first emitted entry instead.
- For G38.2 probing, the final entry for the line reflects the actual trip point if the probe
  tripped, or the commanded endpoint if it did not.
- On error, "entries" contains all motion and state changes that completed successfully,
  including any sub-motions of the failing block that finished before the failure. No entry
  is emitted for the operation that actually failed.
- The trace file is written on both success and error, independently of any other optional
  output file. The relative order in which --output and --trace-output are written on a
  single run is unspecified; both must appear at their configured paths whenever the
  simulator exits, on success or on error. --parameter-output remains governed by its
  success-only rule above and is not written on the error exit path.

## Trace file examples

The examples below illustrate the trace file format on small programs. In each example
"initial_state" is shown abbreviated: a real trace file's "initial_state" must carry every
field required by the --output payload schema (all 9 coordinate systems under
"coordinate_system_offsets", every default modal group under "active_modal_g_codes" and
"active_modal_m_codes", and any parameters loaded from --parameter-input). No real trace file
contains "..." or any placeholder; the ellipses in the examples below mark elided content for
readability only.

### Example 1 -- Linear motion (complete file structure)

Input `program.ngc`:

    G1 X1 F60

Invocation:

    simulator --input program.ngc --output out.json --trace-output trace.json --trace-time-step 0.5

At F60 (60 units/min = 1 unit/second) the 1-unit move takes 1.0 seconds. With
--trace-time-step 0.5, the single interior stepped sample falls at sub-motion-local time 0.5
(strictly less than 1.0), followed by the mandatory final entry at 1.0. No entry is emitted
at time 0.0; the modal and feed_rate deltas declared by the block ride the first emitted
entry (at time 0.5).

`trace.json`:

```json
{
  "initial_state": {
    "machine_position": {"x": 0.0, "y": 0.0, "z": 0.0, "a": 0.0, "b": 0.0, "c": 0.0},
    "feed_rate": 0.0,
    "spindle_speed": 0.0,
    "spindle_direction": "OFF",
    "cutter_radius_compensation_number": null,
    "tool_length_offset_index": null,
    "selected_tool": null,
    "tool_in_spindle": null,
    "active_modal_g_codes": {"1": "G0", "3": "G90", "6": "G20", "...": "other default groups"},
    "active_modal_m_codes": {"4": "M5", "...": "other default groups"},
    "coordinate_system_offsets": {
      "1": {"x": 0.0, "y": 0.0, "z": 0.0, "a": 0.0, "b": 0.0, "c": 0.0},
      "...": "systems 2 through 9 with default zero offsets"
    },
    "parameters": {}
  },
  "entries": [
    {"line_number": 1, "time": 0.5, "feed_rate": 60.0, "active_modal_g_codes": {"1": "G1"}, "machine_position": {"x": 0.5}},
    {"line_number": 1, "time": 1.0, "machine_position": {"x": 1.0}}
  ],
  "error_line_number": null,
  "error_block_segment_index": null
}
```

Points illustrated:
- No entry is emitted at time 0.0. The first emitted entry is the stepped sample at time
  0.5, and it absorbs the line's modal and feed_rate deltas in addition to its position.
- The final entry's "time" equals the line's total duration.

### Example 2 -- Canned cycle G81 with sub-motion expansion

Input (at line 7 of a larger program; prior state has machine_position (0, 0, 2) and
feed_rate 60):

    G81 X5 Y0 Z-3 R0 F60

Invocation uses --trace-distance-step 1000 (a step larger than any sub-motion's path length),
so each sub-motion emits only its final entry with no interior samples. This keeps the
example compact while illustrating the sub-motion structure of a canned cycle.

Sub-motion breakdown (G98 retract to initial plane Z=2):
- SM1: rapid (0,0,2) -> (5,0,2). Path length 5. Duration 5 / (1000/60) = 0.3 s.
- SM2: rapid Z 2 -> 0. Path length 2. Duration 2 / (1000/60) = 0.12 s.
- SM3: feed Z 0 -> -3 at F60. Path length 3. Duration 3 / 1 = 3.0 s.
- SM4: rapid Z -3 -> 2 (retract). Path length 5. Duration 5 / (1000/60) = 0.3 s.
- Total line duration: 0.3 + 0.12 + 3.0 + 0.3 = 3.72 s.

`trace.json` entries for line 7 (initial_state and earlier entries elided):

```json
{
  "entries": [
    {"line_number": 7, "time": 0.3,  "motion_kind": "rapid", "active_modal_g_codes": {"1": "G81"}, "machine_position": {"x": 5.0}},
    {"line_number": 7, "time": 0.42, "motion_kind": "rapid", "machine_position": {"z": 0.0}},
    {"line_number": 7, "time": 3.42, "motion_kind": "feed",  "machine_position": {"z": -3.0}},
    {"line_number": 7, "time": 3.72, "motion_kind": "rapid", "machine_position": {"z": 2.0}}
  ]
}
```

Points illustrated:
- No entry is emitted at time 0.0. The line's modal delta (G81) rides the first emitted
  entry, which is SM1's final entry at cum time 0.3.
- Each sub-motion's first emitted entry carries "motion_kind". Here every sub-motion has
  only its final entry (no interior samples), so every emitted entry carries motion_kind,
  including SM4's final at t=3.72.
- "time" is cumulative within the line (sub-motion durations recoverable by subtraction).

### Example 3 -- Error case

Input `program.ngc`:

    G1 X1 F60
    G43 H99
    G1 X2

Line 2 references H99 without a loaded tool table and is therefore invalid per the
specification. The simulator exits 1 after writing both --output and --trace-output files.

`trace.json`:

```json
{
  "initial_state": {"...": "end-snapshot defaults"},
  "entries": [
    {"line_number": 1, "time": 0.5, "feed_rate": 60.0, "active_modal_g_codes": {"1": "G1"}, "machine_position": {"x": 0.5}},
    {"line_number": 1, "time": 1.0, "machine_position": {"x": 1.0}}
  ],
  "error_line_number": 2,
  "error_block_segment_index": null
}
```

Points illustrated:
- On error the trace file is still written; "entries" contains every entry from successfully
  completed blocks, truncated before the failing operation.
- "error_block_segment_index" is null because G43 H99 is not a multi-sub-motion expansion;
  a G83 peck failing on its third peck would set it to 2 (0-based sub-motion index).
