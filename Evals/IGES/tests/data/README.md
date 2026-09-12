# Frozen reader fixtures

`reader-fixtures.json` stores paired semantic input documents and physical IGES
records. They are **inputs, not expected submission outputs**. Reader, query,
evaluation and reader-error cases copy them without invoking the submission
writer. Explicit writer/semantic-roundtrip tests continue to invoke it.

Each key is SHA-256 of UTF-8 `json.dumps(document, sort_keys=True,
separators=(",", ":"))`. The helper verifies document equality and fails on a
missing entry; it never falls back to a submission-generated input.

## Provenance and independent verification

The initial records were captured on 2026-09-11 from existing test documents,
using the Python reference at commit
`b7e5c1a453c4c3a5575742d624d2bf306764e022` inside image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`.
The original 263 tests passed. Only input documents used by retained independent
probes are kept; writer/roundtrip-only captures were discarded.

Capture alone does not establish conformance. The following changes followed
independent inspection of the model-visible specification:

- On 2026-09-12, the v1.0.17 follow-up independently verified that all 44
  captured Global streams contained illegal `0H` for optional field25.
  §2.2.2.3 requires a nonzero count; §2.2.3 defaults an empty field to NULL.
  Replace that token with an empty field, repack only Global physical records
  and update Terminate counts. Semantic documents/keys and all S/D/P records
  remain identical. The independent validator now scans Hollerith boundaries
  in joined Global streams, so reference acceptance cannot hide this again.
- Uniform Offset Curve PTYPE is zero (§4.25); the paired physical tokens match.
- Type114 ignored boundary slots are explicit in this corpus (§4.15). The new
  2×1 fixture was built directly from its parameter table with ignored values
  123.0, exposing readers that mistake them for the next geometric patch. A
  submission writer may terminate trailing default slots under §2.2.3; the
  scored assertion constrains only actual coefficients and their interleaving.
- Direction123 records have the required physical-dependency status and actual
  Plane190/analytic parents (§4.20).
- Four analytic192–198 input documents were captured on 2026-09-12 using the
  corrected Python reference in the same pinned image. `analytic_support.py`
  computes their exact rational-quadratic/linear boundaries, and
  `topology_support.py` supplies valid Face510/OpenShell514 parents. Independent
  parameter-table, implicit-surface, endpoint and orientation checks validate
  these inputs; reference acceptance is not the geometric oracle.
- Only the five conflicting direct OffsetSurface140-over-192–198 cases were
  removed. Independent Plane190 and legal bounded analytic cases remain.

Run the unscored maintenance checks from the repository root:

```bash
uv run python Evals/IGES/tests/validate_reader_fixtures.py
uv run python Evals/IGES/tests/validate_topology_fixtures.py
```

The first imports no reference implementation and checks **44 documents / 117
entity records**: identity hashes, physical widths/order/sequences, directory
status/type/form links, Parameter Data ranges/back-pointers, terminate counts,
and spec-based numeric parameter order. Type114 compares real patches separately
from arbitrary ignored slots. Analytic inputs also receive independent reference,
loop-closure, rational-curve endpoint and implicit-surface residual checks.
The second independently validates the positive topology fixtures, including
closed-shell opposing edge uses and the contained void. Neither adds score units.

All three reference languages run against the repaired suite in that offline
image. Coordinate expectations in scored tests are independently calculated,
not copied from reference evaluation. See `docs/validation/IGES-1.0.16.md` and `docs/validation/IGES-1.0.17.md` for
results, explicit public conflicts and remaining correlated prerequisites.

For future fixture maintenance, update both semantic documents and physical
records, regenerate keys, run the independent checks, and rerun affected scored
tests. Never automatically refresh these inputs from a submission or treat a
reference writer as an unchecked source of truth.
