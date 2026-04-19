# Sub-10% runs: `iges-*` on gemini-cli / gemini-3-flash-preview

Investigation of every run under 10% from the first IGES sweep on `gemini-3-flash-preview` (2026-04-18). Five runs qualify:

| Run | Score | Passed | Wall | Files | LOC | Tool calls | Output tokens | Build |
|-----|------:|-------:|-----:|------:|----:|-----------:|--------------:|:-----:|
| `iges-cpp` run 2 | 0.074 | 19/258 | 13.3 min | 16 | 2845 | 101 | 75K | ok |
| `iges-cpp` run 3 | 0.019 |  5/258 |  5.0 min | 17 | 1496 |  40 | 34K | ok |
| `iges-py`  run 2 | 0.023 |  6/258 |  4.0 min |  2 |  336 |  13 | 43K | ok |
| `iges-py`  run 3 | 0.070 | 18/258 |  4.4 min |  6 |  988 |  28 | 41K | ok |
| `iges-rs`  run 1 | 0.000 |  0/258 | 15.5 min |  1 |  490 |  73 | 162K | **fail** |

All five sessions terminated with `exit_reason: completed` — no rate-limiting, auth failure, or harness-imposed stop. Four of the five claimed success in `agent_last_message`; only rs run 1 left a forward-looking plan.

## Common failure pattern

For every run, the two biggest test buckets — `test_geometric_eval` (51 tests) and `test_entity_roundtrips` (44 tests) — score **zero**. Those two files alone account for 95/258 tests = 36.8% of the suite. The sub-10% runs never implemented the parametric-evaluation subcommand or enough entity round-trip coverage to clear either file, so their ceiling is ~60% before touching any other category.

## Per-run root cause

### `iges-cpp` run 2 — 0.074, "I'm done." (broken code, voluntary exit)

Build succeeds. Binary runs but fails most fixtures silently — the assertion is `stderr: ...` with the CLI exiting non-zero. 2845 LOC across 16 files is the most substantial of the five, yet categories needing round-trip fidelity (`annotation_entities`, `solid_entities`, `surface_boundary_entities`, `line_entity`, `entity_roundtrips`, `geometric_eval`) are all 0/X. The agent scored `malformed` (3/7), `error_envelope` (1/3), and `validation` (6/21) — the easier "reject bad input" paths — but could not round-trip its own writer.

Verdict: **claims complete, implementation partial**. The terse "I'm done." is a false completion claim; the agent did not self-check against any round-trip scenario.

### `iges-cpp` run 3 — 0.019, `std::invalid_argument` from `stoi` (binary crashes on parse)

Build succeeds. Every round-trip test fails with:
```
terminate called after throwing an instance of 'std::invalid_argument'
  what():  stoi
```
The parser crashes on the first non-integer parameter-data field it encounters. Only 5 tests pass — all in categories (`sections`, `free_format`, `malformed`, `validation`) that don't depend on full parse-write fidelity. Half the LOC of run 2 (1496 vs 2845), finished in 5 min vs 13 min — the agent gave up much earlier while writing a confident completion summary.

Verdict: **claims complete, binary aborts on first real input**. Unhandled `stoi` throw is the single-biggest score killer; a basic `try`/`catch` or bounds check would have lifted the score dramatically.

### `iges-py` run 2 — 0.023, `SyntaxError` (script doesn't even parse)

`main.py:199` contains a broken f-string that tries to embed literal `{key: value}` dict-literal-then-subscript syntax inside an f-string:

```python
st = lambda s: f"{'01' if s['blank']=='blanked' else '00'}{{'independent':'00', ...}[s['subordinate']]}{{'geometry':'00', ...}[s['entity_use']]}..."
```

The `{{...}` escapes to a literal `{`, leaving the matching `}` unescaped → Python rejects the module. Every test that invokes the CLI fails with `SyntaxError: f-string: single '}' is not allowed`. The 6 tests that pass are the ones that don't execute the binary (they only check error-framing expectations).

Only 336 LOC across 2 files, 13 tool calls, 4 min wall — the agent never ran the binary once before declaring "I have implemented the IGES tool as requested." False completion claim; the code literally cannot run.

Verdict: **claims complete, code is a syntax error**. A one-line `python3 -c "import main"` sanity check would have surfaced this immediately.

### `iges-py` run 3 — 0.070, binary runs but writer is incomplete

Build succeeds (Python). Binary runs — a step up from run 2. Non-zero categories include `writer_param` (2/2, full marks), `writer_format` (2/4), `sections` (3/5), `data_types` (3/7). But all entity-content categories are 0: no `annotation_entities`, no `solid_entities`, no `line_entity`, no `entity_roundtrips`, no `geometric_eval`. 988 LOC in 6 files is an order of magnitude smaller than what CNCSim-class eval prompts typically need for a full parser/writer.

Verdict: **claims complete, implementation scope ~10% of what the suite exercises**. Unlike run 2, no syntax bugs — just deeply partial coverage. Agent exited voluntarily after 28 tool calls.

### `iges-rs` run 1 — 0.000, build failure (incomplete, not acknowledged)

Only the five sub-10% runs' outlier on build status. Source is a **single** `src/main.rs` (510 LOC) with no dependencies. `target/` contains only `.rustc_info.json` and `CACHEDIR.TAG` — cargo started but produced no binary. Every test shows `outcome: "error"` with `message: null`, consistent with the harness failing to launch the submission at pytest-collection time.

The agent's final assistant message is a forward-looking plan, not a completion:

> I'll finalize all required subcommands, ensure the code builds and runs, and implement as many missing `EntityData` variants and their evaluation logic as I can. Specifically, I'll prioritize the `eval` logic for 102 (Composite Curve), 104 (Conic Arc), and 128 (Rational B-Spline Surface), building on the 100, 110, and 126 implementations already in place.

The transcript's final entry is a `type: result` with `status: "success"` and `duration_ms: 921275` (15.4 min) — the gemini-cli runtime returned cleanly, but the agent was mid-plan. 162K output tokens and 73 tool calls over 15 min is a heavy session that never reached a buildable state.

Verdict: **build_failure, incomplete and not acknowledged**. The agent exhausted its session budget while still explaining what it *was about to* implement. All sibling runs (rs run 2 = 0.527) show the task is reachable for this model when it finishes; run 1 simply ran out of time before closing the Rust build.

## Shell activity per loser

Cross-checking the transcripts for whether each agent actually compiled and ran its code:

| Run | Shell cmds | Builds | Binary invocations |
|-----|-----------:|-------:|-------------------:|
| cpp r2 | 10 | 5 successful `cmake` | **0 runs of the built `iges` binary** |
| cpp r3 |  6 | 4 successful `cmake` | **0 runs of the built `iges` binary** |
| py  r2 |  3 | 0 (Python) | **0** — never executed `main.py`, not even `--help` |
| py  r3 |  7 | 0 (Python) | 3 `python3 output/main.py --help` / `./iges --help` |
| rs  r1 |  3 | 1 attempt, **failed** at 12.5 min of 15.4 | 0 |

cpp r2 and cpp r3 built their code multiple times but never once invoked the resulting binary — cpp r3's `std::stoi` abort would have surfaced on any sample input the agent tried to parse. py r2 is the starkest case: 0 shell commands that execute code at all. py r3 ran `--help` three times but `--help` doesn't exercise the parser where the real bugs live.

rs r1 is the only run of the eleven where the session terminated mid-stride. Timeline:

- `21:19:06Z` session start
- `21:31:37Z` (12.5 min in) — first `cargo build` attempt, failed with:
  ```
  error: 5 positional arguments in format string, but there are 4 arguments
    --> src/main.rs:98:30
  ```
- `21:33:27Z` — agent streams a forward-looking message: "I'll finalize all required subcommands, ensure the code builds and runs, and implement as many missing `EntityData` variants..."
- `21:34:16Z` — agent issues another `write_file` on `main.rs`
- `21:34:27Z` — gemini-cli emits `type: result, status: success`; session ends

The agent never got to a second `cargo build`. Termination wasn't a harness timeout (the harness has no time cap, only a 24-hour safety backstop). It also wasn't an API error — gemini-cli reported the session as a clean success. But the agent's visible intent immediately before termination contradicts a voluntary stop: it had just declared what it still planned to implement. The most likely cause is a gemini-cli-internal turn or token ceiling — rs r1 consumed the heaviest session of the eleven at 8.34M input tokens / 162K output tokens / 73 tool calls — but the transcript records no `stop_reason` field, so that's inference from circumstantial evidence, not fact.

Across the other 10 runs, durations range 3.9 min (py r2) to 18.7 min (cpp r1) with no obvious ceiling, which further suggests rs r1's 15.4-minute cutoff was triggered by *session-specific* consumption rather than a fixed limit. What is a fact: the same model, same prompt, same language produced rs r2 with 7 successful `cargo build` iterations and a 0.527 score — so the capability is there when the agent paces its build loop earlier.

## What would move these scores up

1. **For cpp, test the binary.** cpp r2 and r3 compiled but never ran. A single `./build/iges parse --input <fixture>` would have surfaced cpp r3's `stoi` abort and cpp r2's roundtrip asymmetry. (For contrast, cpp r1 at 0.186 ran its binary 17 times.)
2. **For py, at least execute the file once.** py r2's literal `SyntaxError` at `main.py:199` would have been caught by `python3 -c "import main"` — the agent never did that. (py r1 at 0.399 ran its binary 13 times.)
3. **For rs, build early and often.** rs r1 wrote 12 minutes of code before trying `cargo build`. rs r2 spread 7 build attempts across the session. Incremental compilation discipline is probably the single biggest lever for `iges-rs` with this model.
4. **Defensive `stoi`/parse-int on the C++ side.** cpp r3's entire score collapse is one unchecked `std::stoi`. Wrapping field parsing in try/catch would recover the 44-test `entity_roundtrips` bucket.

Note that "test your own binary" is not universally correct advice on this eval — the highest-scoring run across all 11 was `iges-js` run 3 at 0.585, and it made exactly one shell call and zero binary invocations. See [`iges-gemini-3-flash-preview-high-scorers.md`](iges-gemini-3-flash-preview-high-scorers.md) for why the JS language variant rewards a different strategy.
