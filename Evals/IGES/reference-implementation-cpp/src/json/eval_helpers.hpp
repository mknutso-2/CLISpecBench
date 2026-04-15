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

} // namespace iges
