# IGES 1.0.16 scoring audit — 2026-09-12

All model-visible prompt files, the supplied IGES specification and shared
language inputs are unchanged. The hidden suite has **260 cases** (263 − 5
conflicting cases + 2 Type114 regressions). Python/JavaScript reference fixes
address Type114 physical patch layout; the C++ reference already handles it.

## Findings and corrections

The v1.0.14 `.get()` migration left repeated `ok` assertions in behavioral tests.
Successful geometry and input rejection now require the relevant observation
(point or diagnostic) while dedicated schema gates own exact metadata fields.
CLI output paths are removed before invocation, preventing a repeated probe from
reading stale success. Decoded payloads must be objects before object access.
Missing output or incorrect geometry does not earn credit.

Many reader/evaluator probes previously invoked the submission writer to create
input, so a writer bug blocked unrelated parser/query/evaluation observations.
These probes now read frozen input files. Actual writer tests and explicit
semantic roundtrips still use the submission writer. The corpus contains 44
reviewed documents / 117 entity records, with provenance and independent checks
in `Evals/IGES/tests/data/README.md`.

Independent inspection found invalid positive fixtures that permissive references
had accepted. Repairs preserve the existing target observations:

- CircularArc100 start/end radii agree (§4.3). Types118/120/122/130/140 have
  actual supporting curves/surfaces, with valid pointer types and domains.
  Uniform OffsetCurve130 unused NDIM/PTYPE fields are zero (§4.25).
- Direction123 is physically dependent and has a genuine referencing parent
  (§4.20). Independent Plane190 is explicitly legal (§4.50); its pointer-backed
  geometry remains covered, including Form0 and transformed evaluation.
- Types192/194/196/198 have nondegenerate finite Face510/OpenShell514 parents.
  Twelve existing roundtrip/eval cases remain. Exact rational quadratic arcs and
  lines form closed boundaries lying on the analytic surfaces. Independent
  residual, endpoint and normal/tangent orientation checks validate all eight
  type/form fixture combinations, including the torus minus-Y convention.
- Six topology roundtrips now use a valid open triangular shell and a closed
  tetrahedral solid with a disjoint internal void. Form/dependency/hierarchy,
  actual curves/vertices, closure, face area and opposing shell edge uses satisfy
  §§4.49 and 4.143–4.147. Target-only comparisons retain orientation and nested
  parameter-curve observations.
- Six surface-boundary/group positives now have a real bilinear128 surface and
  matching model/parameter curves, proper usage/dependency flags, valid loops,
  disjoint clockwise holes, and a Form7 group that needs no unavailable member
  back-pointer (§§4.31–4.34 and 4.85). Their ten collected cases are unchanged.
- Eight pointer-field positives now use real referenced records. The Plane108
  nonzero-pointer regression uses bounded Form1 and a simple closed circle;
  unbounded Form0 explicitly requires PTR=0 (§4.12). FE cases have labeled
  Form10 coordinate systems, matching node/element subscript IDs, actual case
  notes and a two-node BEAM (§§4.21, 4.27–4.29, 4.35–4.36). Network definitions
  and instances have matching ConnectPoint ownership, actual display templates,
  and zero nesting depth. NodalLoad418 references actual constant PTYPE12
  tabular properties. Only the target fields are compared.
- Metadata positives now provide real subfigure/font/display/solid targets
  (304→308→110, 312→310, 322→312, 430→158). Type302 uses an implementor Form5001;
  300-series records have Definition use, font/color definitions have legal
  fallbacks, and Type316 uses listed M/KG unit names with scale0.001. These
  nine cases keep their IDs and target observations (§§2.2.4.4.9, 4.69–4.77,
  4.142 and the technical appendix).

Numeric comparisons also mixed exact real equality, pytest's default relative
1e-6 tolerance and absolute-only geometric checks. TR §3 instead defines
semantic reals at relative1e-12/absolute1e-15 and evaluated coordinates at
relative1e-9/absolute1e-12. Those public limits are now explicit. Recursive
semantic equality preserves exact shape/discrete values and excludes bool from
real leaves. Two circular-midpoint observations compare exact analytic
coordinates directly instead of combining returned coordinates into squared
residuals, which can amplify permitted error or accept the wrong arc angle.

The Type114 spline tests had only one patch row. Python/JavaScript references
read and wrote M*N coefficient blocks contiguously, omitting the ignored
48-coefficient boundary column between rows (§4.15). A new independent 2×1 input
uses nonzero ignored values and X=u, Y=v, Z=max(u−1,0)^2; separate tests observe
second-row evaluation and physical writer coefficient placement. The references
now skip/emit those slots. The writer assertion permits blank/defaulted real
values and §2.2.3 termination of trailing defaults; it does not require arbitrary
ignored slots to have a specific value or spelling.

A core-arc test name now describes the start point it actually measures; its
coordinate observation is unchanged.

## Five conflicting public requirements deferred

Technical requirements §1.6 explicitly supports OffsetSurface140 with analytic
192/194/196/198 bases. The supplied IGES §§4.51–4.54 simultaneously say those
four types can only be referenced by Face510. No public precedence rule resolves
that direct-reference conflict. Adding a valid Face cannot legalize another
prohibited direct reference from an OffsetSurface.

Only the five direct-analytic-offset cases below are excluded from collection;
they add neither passes nor denominator entries. All other analytic cases have
legal topology and remain scored. Plane190-based offset coverage remains because
§4.50 permits independent planes and does not contain the Face-only restriction.
Source for the five excluded cases remains in Git history.

A future public revision should explicitly choose whether analytic offset bases
relax those full-spec restrictions or should use alternative supported surfaces.
That public behavioral choice needs new model runs. A perfect current score does
not establish conformance for the five deferred combinations.

Excluded node IDs (under `Evals/IGES/tests/`):

- `test_geometric_eval.py::test_offset_surface_over_cylinder_expands_radius_on_indicator_side`
- `test_geometric_eval.py::test_offset_surface_indicator_flips_global_normal_orientation`
- `test_geometric_eval.py::test_offset_surface_over_cone_uses_conical_reference_parameters`
- `test_geometric_eval.py::test_offset_surface_over_sphere_extends_radius_along_spherical_normal`
- `test_geometric_eval.py::test_offset_surface_over_torus_offsets_along_minor_circle_normal`

## Remaining public documentation limitations

The technical appendix illustrates Type316 length units with MM, whereas the
supplied §4.77 list names M and a scale factor. Positive fixtures now use their
unambiguous intersection (M, scale0.001); a later public revision should align
that example with the table. No new rejection rule for MM is scored.

Several FE/network sections are intentionally omitted from the supplied mirror.
Type418's technical appendix exposes node and tabular-property pointers, while
§3.7 prose also mentions case General Notes without an exposed slot. Its test
checks the available typed pointer fields using real PTYPE12 records; it does
not require an unexpressible note field. Network tests likewise stay within
public appendix schemas and the supplied ConnectPoint rules. These tests do
not establish full conformance to omitted sections.

## Validation and limits

Full reference and mutation runs use grader image
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`,
with the repository read-only and Docker networking disabled.

| Control | Result |
| --- | --- |
| Original Python reference / original suite | 263/263 |
| Corrected Python reference / repaired suite | 260/260 |
| Unchanged C++ reference / repaired suite | 260/260 |
| Corrected JavaScript reference / repaired suite | 260/260 |
| Original Python reference / new Type114 tests (host) | 0/2 |
| Original JavaScript reference / new Type114 tests (host) | 0/2 |
| Valid writer omitting trailing ignored Type114 slots | 2/2 |
| Legal sub-tolerance perturbations to all real/coordinate outputs | 260/260 |
| Every JSON `ok` field removed | 255/260 |
| Every `write` command immediately fails | 120/260 |
| Point X corrupted by +1, geometry/line/layout subset | 44 failures / 57 cases |
| Six separate target topology-output corruptions | Each 1 intended failure / 6 cases |
| Four separate metadata pointer-loss corruptions | Each 1 intended failure / 9 cases |
| Eight separate pointer-field corruptions | Each 1 intended failure / 8 cases |

The sub-tolerance wrapper adds relative2e-13/absolute2e-16 to semantic real
outputs and relative2e-10/absolute2e-13 to evaluated coordinates, within their
respective published limits. All260 cases pass. Focused helper controls accept
integer JSON spelling for real expectations, reject bool in real/discrete
numeric fields, reject shape changes and reject outside-tolerance differences.

All five missing-`ok` failures are dedicated schema gates. All 44 coordinate
observations in the focused subset fail incorrect points; the other 13 cases
measure different properties. Six topology mutations independently corrupt a
vertex coordinate, edge vertex index, loop orientation, face outer-loop flag,
shell face orientation, or solid void orientation; each fails only its target
roundtrip among those six observations. Four metadata pointer-loss controls and
all eight pointer-field controls likewise fail exactly their intended test,
leaving their respective eight or seven neighboring cases passing.

The broken-writer control retains 120 measurable observations and fails 140
writer/integration cases. Those 140 failures are **not 140 independent bugs**.
Frozen inputs remove a writer prerequisite; they do not remove shared parser or
supporting-entity prerequisites. Legal analytic/topology files contain actual
Face/OpenShell and curve/vertex records. A parser unable to handle those support
types can still produce correlated failures. Full semantic roundtrips can also
share mutually consistent parser/writer bugs. The audit improves signal but does
not establish complete coverage, statistical independence or lack of saturation.

Ruff and strict Pyright pass for `Evals/IGES/tests` (Pyright uses the repository
virtualenv and task-local imports). Python reference compilation and JavaScript
syntax checks pass. Reference Python is intentionally excluded from the repo's
harness style/type scopes and is validated behaviorally. Independent unscored
validators check all 44 frozen inputs/117 records, the 13-entity open triangle,
the 67-entity solid/void graph, and repaired surface-boundary fixture geometry.
A separate reviewer checked curved boundary orientation for all eight analytic
kind/form combinations; another reviewed topology and surface-boundary repairs.

Reference/mutation reports and capture drivers remain in this workstation's
`work/engineering-audit/`, `work/records-topology/`, and
`work/non-rs274-audit/` scratch directories. Original reference controls came from
commit `b7e5c1a453c4c3a5575742d624d2bf306764e022`. No historical published scores
were overwritten by the audit. Old non-RS274 generated source artifacts were
unavailable locally; fresh missing-model runs are separate from these controls.

Unscored physical/geometry maintenance commands, from the repository root:

```sh
python3 Evals/IGES/tests/validate_reader_fixtures.py
python3 Evals/IGES/tests/validate_topology_fixtures.py
```

The surface-boundary and curved-analytic independent checkers are preserved as
`work/non-rs274-audit/validate_surface_fixtures.py` and
`work/records-topology/check_analytic.py` on this workstation. None contributes
scored pytest cases.
