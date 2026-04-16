#pragma once
// iges::ConicArcEntity — Type 104.

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <utility>

namespace iges {

struct ConicArcEntity {
    // Coefficients: A*X^2 + B*X*Y + C*Y^2 + D*X + E*Y + F = 0
    Real A = 0.0;
    Real B = 0.0;
    Real C = 0.0;
    Real D = 0.0;
    Real E = 0.0;
    Real F = 0.0;

    Real zt = 0.0;   // Z coordinate of the plane

    Real x1 = 0.0;   // Start point X
    Real y1 = 0.0;   // Start point Y
    Real x2 = 0.0;   // Terminate point X
    Real y2 = 0.0;   // Terminate point Y

    // Discriminant quantities per spec:
    // Q1 = det |A   B/2 D/2|
    //          |B/2 C   E/2|
    //          |D/2 E/2 F  |
    // Q2 = A*C - (B/2)^2
    // Q3 = A + C
    Real Q1() const;
    Real Q2() const;
    Real Q3() const;

    // Classification per spec:
    // Ellipse: Q2 > 0 and Q2*Q3 < 0
    // Hyperbola: Q2 < 0
    // Parabola: Q2 == 0 and Q1 != 0
    bool is_ellipse() const;
    bool is_hyperbola() const;
    bool is_parabola() const;

    // Evaluate the spec's default parameterization in definition space.
    Vec3 evaluate(Real t) const;

    // Native parameter interval [t1, t2] from the entity's start and
    // terminate points, following the §4.5 default parameterization.
    std::pair<Real, Real> parameter_span() const;
};

std::expected<ConicArcEntity, Diagnostic>
parse_conic_arc_entity(ParamTokenizer& tok);

} // namespace iges
