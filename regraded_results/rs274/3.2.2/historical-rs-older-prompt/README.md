# Historical Rust RS274 regrades — older prompt sub-cohort

51 published `rs274-rs` submissions regraded under the v3.2.2 rubric. Generation eval is
**3.1.11**; grading eval is **3.2.2**.

**These rows are separated from [`../historical/`](../historical/README.md) for a reason that has
nothing to do with grading.** They were generated against Rust prompt
`35713dbfd826…`, not the current `1290cae737822462343abb2a1b7ab533b3ce2ae10a59b78758b5a16da395d7ae`.
Every record therefore carries `comparison.model_input_unchanged: false`, with both digests
recorded under `generation_prompt_content_sha` and `current_prompt_content_sha`.

So these submissions differ from the rest of the record on **two** axes at once — the model saw
different instructions *and* the tests changed — while every other migrated row differs on the
grading axis alone. Do not pool them with same-prompt Rust rows in a ranking, and state the prompt
difference wherever they appear beside one.

Affected models: claude-haiku-4-5, claude-opus-4-5/4-6/4-7, claude-sonnet-4-5/4-6, gpt-5.2,
gpt-5.3-codex, gpt-5.4, gpt-5.4-mini, gpt-5.5, gemini-3-flash-preview, gemini-3.1-pro-preview.

## Environment

- Test suite SHA-256: `3d096665fab1578444b0c0a0f7bfa1975e389a9398a34e265820305b300eca11`
- Docker image: `sha256:922c3bc7435e5546e737bf77b5bc8c07d15f86c9bad7f6fc68555cf8fbf04dc5`
- Every record: 555 collected tests, no skips, no pytest infrastructure errors
- Selected by published run UID, never by score

Grading concurrency, its verification, and the percent-framing effect that drives much of the
score movement are documented in the [`historical` cohort README](../historical/README.md) and
apply identically here.

## Provenance

Each record is a `clispecbench.regrade-summary` with complete per-test outcomes, subscores and
provenance; source archives and raw pytest reports are excluded. Original UIDs, scores and
token/cost accounting are retained. Additional model calls and model cost are zero. These are
grading observations, not new model trials, and no published record is modified.
