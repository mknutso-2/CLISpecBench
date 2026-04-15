#pragma once
// iges::ParametricSplineSurfaceEntity — Type 114.

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

// 48 coefficients per patch: 16 for X, 16 for Y, 16 for Z.
// X(u,v) = sum_{p=0}^{3} sum_{q=0}^{3} coeff_x[4*p+q] * s^q * t^p
// where s = u - TU(i), t = v - TV(j)
struct SplineSurfacePatch {
    Real coeff_x[16] = {};  // AX,BX,CX,DX, EX,FX,GX,HX, KX,LX,MX,NX, PX,QX,RX,SX
    Real coeff_y[16] = {};
    Real coeff_z[16] = {};
};

struct ParametricSplineSurfaceEntity {
    int ctype = 0;    // Spline boundary type
    int ptype = 0;    // Patch type: 0=unspecified, 1=Cartesian product
    int M = 0;        // Number of u segments
    int N = 0;        // Number of v segments

    std::vector<Real> tu;  // M+1 u breakpoints
    std::vector<Real> tv;  // N+1 v breakpoints

    // M*N patches stored row-major: patch(i,j) at index i*N + j
    std::vector<SplineSurfacePatch> patches;

    // Evaluate surface at (u,v).
    Vec3 evaluate(Real u, Real v) const;
};

std::expected<ParametricSplineSurfaceEntity, Diagnostic>
parse_parametric_spline_surface_entity(ParamTokenizer& tok);

} // namespace iges
