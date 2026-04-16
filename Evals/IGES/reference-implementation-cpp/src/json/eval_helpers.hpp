#pragma once
// iges::eval_helpers — resolver-using evaluators for IGES entities whose
// `iges eval` semantics depend on other entities referenced by DE index.
//
// The auto-generated `evaluate_entity_dispatch` routes a fixed set of
// "resolver-using" type numbers (102, 130, 118, 120, 122, 140) to the
// free functions declared here. Simple self-contained entities (Line,
// Circular Arc, B-Spline, etc.) stay inline in dispatch.cpp.

#include "dispatch.hpp"
#include "../entities/composite_curve_entity.hpp"
#include "../entities/offset_curve_entity.hpp"
#include "../entities/ruled_surface_entity.hpp"
#include "../entities/surface_of_revolution_entity.hpp"
#include "../entities/tabulated_cylinder_entity.hpp"
#include <utility>

namespace iges {

// Returns the native parameter domain `[t_min, t_max]` of a curve entity
// as defined in §4 of the IGES 5.3 spec (see `§1.6` of the agent
// contract doc for the per-type conventions). Used by Composite Curve
// (§4.4) to accumulate constituent parameter lines.
//
// Supports curves whose domain is fully determined by the parsed JSON:
//   * Type 100 Circular Arc — [start_angle, terminate_angle]
//   * Type 106 Copious Data (forms 11/12/63) — [0, N−1]
//   * Type 110 Line — [0, 1]
//   * Type 126 Rational B-Spline Curve — [v0, v1]
// Other curve types return an error (either unsupported or domain is
// itself resolver-dependent).
std::expected<std::pair<Real, Real>, Diagnostic>
curve_native_span(int type, int form, nlohmann::json const& data);

// Composite Curve (Type 102) default-parameterization evaluator (§4.4).
//
// Builds the cumulative parameter line
//     T(0) = 0,  T(i+1) = T(i) + (v1_i − v0_i)
// where `[v0_i, v1_i]` is the native parameter domain of constituent
// CC(i), then dispatches to the constituent containing `t` at its
// native local parameter.
std::expected<EvalResult, Diagnostic>
evaluate_composite_curve(CompositeCurveEntity const& ent,
                         Real t,
                         EntityResolver const& resolver);

// Offset Curve (Type 130) evaluator (§4.25).
//
// Implements FLAG=1 (uniform offset): evaluates the base curve at the
// native parameter `t ∈ [TT1, TT2]` and displaces by
// `d1 · (VX, VY, VZ)`. FLAG=2 (linear variation) and FLAG=3 (function
// curve) are rejected with a diagnostic — they are not required by
// §1.6 and their data-curve dependency is out of scope for v0.
std::expected<EvalResult, Diagnostic>
evaluate_offset_curve(OffsetCurveEntity const& ent,
                      Real t,
                      EntityResolver const& resolver);

// Ruled Surface (Type 118) evaluator (§4.17).
//
// Surface parameterization: `u = t` runs along the two defining curves,
// `v = s` runs across the rule (v=0 on curve 1, v=1 on curve 2).
//
// * Form 0 (default): `u ∈ [0, 1]` is a normalized fraction. Each
//   curve's sample is at native `v0_i + u · (v1_i − v0_i)`.
// * Form 1 (native): `u` is directly in each curve's native
//   parameter domain (both domains are required to match per §4.17).
//
// `dirflg=1` reverses the second curve's traversal (matches curve 1's
// start to curve 2's end).
std::expected<EvalResult, Diagnostic>
evaluate_ruled_surface(RuledSurfaceEntity const& ent,
                       int form,
                       Real t,
                       Real s,
                       EntityResolver const& resolver);

// Surface of Revolution (Type 120) evaluator (§4.18).
//
// Evaluates the generatrix at native parameter `t`, then rotates the
// resulting point around the axis line by angle `s ∈ [SA, TA]`. The
// axis entity must be Type 110 Line; its two endpoints define the
// axis line in 3D (direction = terminate − start).
std::expected<EvalResult, Diagnostic>
evaluate_surface_of_revolution(SurfaceOfRevolutionEntity const& ent,
                               Real t,
                               Real s,
                               EntityResolver const& resolver);

// Tabulated Cylinder (Type 122) evaluator (§4.19).
//
// Evaluates the directrix at native parameter `t`, then translates by
// `s ∈ [0, 1]` along the generatrix vector
//     terminate_point − directrix_start_point
// where the directrix start point is the point on the directrix at the
// start of its native parameter domain.
std::expected<EvalResult, Diagnostic>
evaluate_tabulated_cylinder(TabulatedCylinderEntity const& ent,
                            Real t,
                            Real s,
                            EntityResolver const& resolver);

} // namespace iges
