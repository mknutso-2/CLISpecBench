#pragma once
// iges::RationalBSplineCurveEntity — Type 126.
//
// §4.23: "The rational B-spline curve may represent analytic curves
//   of general interest."

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct RationalBSplineCurveEntity {
    int K = 0;  // Upper index of sum (number of control points = K+1)
    int M = 0;  // Degree of basis functions

    // Property flags
    int prop1 = 0;  // 0 = nonplanar, 1 = planar
    int prop2 = 0;  // 0 = open, 1 = closed
    int prop3 = 0;  // 0 = rational, 1 = polynomial
    int prop4 = 0;  // 0 = nonperiodic, 1 = periodic

    std::vector<Real> knots;          // length = A+1 where A = N+2*M, N = 1+K-M
    std::vector<Real> weights;        // length = K+1
    std::vector<Vec3> control_points; // length = K+1

    Real v0 = 0.0;  // Starting parameter value
    Real v1 = 1.0;  // Ending parameter value

    Vec3 plane_normal = {0, 0, 0};  // Unit normal if planar (PROP1=1)

    // Derived quantities
    int N() const { return 1 + K - M; }
    int A() const { return N() + 2 * M; }

    // Evaluate the B-spline curve at parameter t using de Boor's algorithm
    Vec3 evaluate(Real t) const;
};

std::expected<RationalBSplineCurveEntity, Diagnostic>
parse_rational_bspline_curve_entity(ParamTokenizer& tok);

} // namespace iges
