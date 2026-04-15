#pragma once
// iges::ParametricSplineCurveEntity — Type 112.

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct SplineCurveSegment {
    Real ax = 0.0, bx = 0.0, cx = 0.0, dx = 0.0;
    Real ay = 0.0, by = 0.0, cy = 0.0, dy = 0.0;
    Real az = 0.0, bz = 0.0, cz = 0.0, dz = 0.0;
};

struct ParametricSplineCurveEntity {
    int ctype = 0;   // Spline type: 1=Linear,2=Quadratic,3=Cubic,4=WF,5=MWF,6=B-spline
    int H = 0;       // Degree of continuity w.r.t. arc length
    int ndim = 3;    // Number of dimensions: 2=planar, 3=nonplanar

    std::vector<Real> breakpoints;           // N+1 breakpoints: T(1)..T(N+1)
    std::vector<SplineCurveSegment> segments; // N segments

    // Terminate point derivatives (evaluated at u = T(N+1))
    Real tpx0 = 0.0, tpx1 = 0.0, tpx2 = 0.0, tpx3 = 0.0;
    Real tpy0 = 0.0, tpy1 = 0.0, tpy2 = 0.0, tpy3 = 0.0;
    Real tpz0 = 0.0, tpz1 = 0.0, tpz2 = 0.0, tpz3 = 0.0;

    // Evaluate curve at parameter u.
    Vec3 evaluate(Real u) const;
};

std::expected<ParametricSplineCurveEntity, Diagnostic>
parse_parametric_spline_curve_entity(ParamTokenizer& tok);

} // namespace iges
