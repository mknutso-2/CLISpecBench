#pragma once
// iges::RationalBSplineSurfaceEntity — Type 128.
//
// §4.24: "The rational B-spline surface represents various
//   analytical surfaces of general interest."

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct RationalBSplineSurfaceEntity {
    int K1 = 0;  // Upper index of first sum
    int K2 = 0;  // Upper index of second sum
    int M1 = 0;  // Degree of first set of basis functions
    int M2 = 0;  // Degree of second set of basis functions

    // Property flags
    int prop1 = 0;  // 1 = closed in first parametric direction
    int prop2 = 0;  // 1 = closed in second parametric direction
    int prop3 = 0;  // 0 = rational, 1 = polynomial
    int prop4 = 0;  // 1 = periodic in first parametric direction
    int prop5 = 0;  // 1 = periodic in second parametric direction

    std::vector<Real> knots_u;         // first knot vector, length A+1
    std::vector<Real> knots_v;         // second knot vector, length B+1
    std::vector<Real> weights;         // C values, stored (K1+1)*(K2+1)
    std::vector<Vec3> control_points;  // C triples, stored (K1+1)*(K2+1)

    Real u0 = 0.0, u1 = 1.0;  // parameter range in U
    Real v0 = 0.0, v1 = 1.0;  // parameter range in V

    // Derived quantities
    int N1() const { return 1 + K1 - M1; }
    int N2() const { return 1 + K2 - M2; }
    int A()  const { return N1() + 2 * M1; }
    int B()  const { return N2() + 2 * M2; }
    int C()  const { return (1 + K1) * (1 + K2); }

    // Access weight/control point at grid position (i, j)
    // Storage order: first index (u direction) varies fastest
    Real& weight(int i, int j) { return weights[j * (K1 + 1) + i]; }
    Real  weight(int i, int j) const { return weights[j * (K1 + 1) + i]; }
    Vec3& control_point(int i, int j) { return control_points[j * (K1 + 1) + i]; }
    Vec3 const& control_point(int i, int j) const { return control_points[j * (K1 + 1) + i]; }

    // Evaluate the surface at parameters (u, v)
    Vec3 evaluate(Real u, Real v) const;
};

std::expected<RationalBSplineSurfaceEntity, Diagnostic>
parse_rational_bspline_surface_entity(ParamTokenizer& tok);

} // namespace iges
