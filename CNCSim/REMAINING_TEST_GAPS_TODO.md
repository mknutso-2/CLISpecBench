# CNCSim Remaining Test Gaps

This file captures the full superset of notable test-gap findings raised during
the recent CNCSim coverage review. It is intentionally broader than the current
consensus shortlist.

## Directly Testable Remaining Gaps

- [ ] Add expression math-domain error tests.
  - Division by zero
  - `SQRT` of a negative
  - `LN` of zero or a negative number
  - `ACOS` / `ASIN` outside `[-1, 1]`
  - Current related coverage:
    - [test_parameter_expressions.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_parameter_expressions.py)
    - [test_parameter_errors.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_parameter_errors.py)

- [ ] Add `MSG` comment coverage.
  - Acceptance/parsing for `(MSG,...)`
  - Any explicit malformed cases if RS274 is unambiguous
  - Current related coverage:
    - [test_comment_parsing.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_comment_parsing.py)
    - [test_comment_errors.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_comment_errors.py)

- [ ] Add implicit motion success-path coverage.
  - Positive case where a block with only axis words continues the active motion mode
  - Current related error-path coverage:
    - [test_linear_motion_errors.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_linear_motion_errors.py#L31)
    - [test_arc_errors.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_arc_errors.py#L49)

- [ ] Add probing-variant coverage for `G38.3`, `G38.4`, and `G38.5`.
  - Current probing coverage only exercises `G38.2`:
    - [test_probing.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_probing.py)
    - [test_probing_errors.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_probing_errors.py)

- [ ] Add `G88` success-path coverage.
  - Current state:
    - error-path coverage exists in [test_canned_cycle_errors.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_canned_cycle_errors.py#L241)
    - positive-path coverage is explicitly omitted in [test_canned_cycles.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_canned_cycles.py#L342)

- [ ] Add explicit `M6` spindle-stop / “no other changes” postcondition coverage.
  - Candidate checks:
    - `M6` forces `spindle_direction == "OFF"`
    - `M6` does not silently change other unrelated observable state
      (excluding the separately rejected `M6`-cancels-TLC claim)

- [ ] Add explicit positive coolant-state coverage for `M7`, `M8`, and `M9`.
  - Current coverage is mostly group-conflict and modal-acceptance oriented.
  - Add a direct positive test for the observable coolant-group state that the payload exposes.

- [ ] Add direct ordinary-motion coverage while `G43` stays active.
  - Current `G43` use is strongest in probing tests, but there is still no direct non-probing `G0` / `G1` coverage that verifies ordinary motion remains shifted while tool length compensation stays active.

## Explicit RS274 Areas Still Weakly Covered Because of Observability / Hardware / Timing Limits

- [ ] Revisit `M0` / `M1` / `M60` behavioral stop/resume semantics and the pallet-shuttle half of `M30`.
  - Current coverage is mostly acceptance/modal tracking:
    - [test_active_mcode_groups.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_active_mcode_groups.py#L69)

- [ ] Revisit `M48` / `M49` actual override-switch effects.
  - Current coverage is modal/reset oriented, not hardware-effect oriented.

- [ ] Revisit `G4` dwell timing.
  - Current positive coverage only checks acceptance and unchanged final state:
    - [test_g4_dwell.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_g4_dwell.py#L8)

- [ ] Revisit `G83` peck sub-move behavior.
  - Final state is checked, but the actual peck sequence is still in the intra-line / sub-move bucket.

## Earlier Candidate Gaps That Currently Look Closed, Incorrect, or Overstated

- [ ] Re-check and keep closed unless new contrary evidence appears: `G53` positive validation.
  - Already covered in [test_position_tracking.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_position_tracking.py#L107)

- [ ] Re-check and keep closed unless new contrary evidence appears: `G40` same-line exit behavior.
  - Already covered in [test_cutter_radius_compensation.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_cutter_radius_compensation.py#L151)

- [ ] Re-check and keep closed unless new contrary evidence appears: `G93` / `G94` transition semantics.
  - Already covered in [test_feed_rate_mode.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_feed_rate_mode.py#L45)

- [ ] Keep rejected unless new RS274 evidence appears: `M6` cancels tool length compensation.
  - Earlier claim was later retracted.

- [ ] Re-check and keep closed unless new contrary evidence appears: “CRC only tests entry move”.
  - Current suite already includes follow-on straight, convex/concave, and arc cases:
    - [test_cutter_radius_compensation.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_cutter_radius_compensation.py)
    - [test_cutter_radius_compensation_errors.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_cutter_radius_compensation_errors.py)

- [ ] Re-check and keep closed unless new contrary evidence appears: rotary `G91` accumulation as a major gap.
  - Current suite already has explicit incremental `A/B/C` coverage:
    - [test_position_tracking.py](C:/Git/SWE-BuildBench/CNCSim/tests/test_position_tracking.py#L168)

- [ ] Keep downgraded unless a concrete ordering-sensitive scenario is identified: same-block execution order as a large remaining gap.
  - Current suite appears to exercise many ordering interactions implicitly.
  - Do not re-promote this to a major gap without a specific order-dependent failure mode.

## Second-Tier Candidates Raised by Explorer Subagents

- [ ] Revisit whether any additional second-tier items remain after the consensus reclassification above.

## Consensus Status

- [x] Re-ran a targeted Claude reconciliation pass on the disputed items and reached consensus on the current bucketing.
