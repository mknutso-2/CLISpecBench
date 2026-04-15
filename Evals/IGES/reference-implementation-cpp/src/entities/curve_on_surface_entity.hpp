#pragma once
// iges::CurveOnParametricSurfaceEntity — Type 142.
//
// §4.32: "The Curve on a Parametric Surface Entity associates a
//   given curve with a surface and identifies the curve as lying
//   on the surface."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct CurveOnParametricSurfaceEntity {
    int crtn = 0;         // Creation method: 0=unspecified, 1=projection,
                          //   2=intersection, 3=isoparametric
    DEIndex sptr;         // Pointer to surface S
    DEIndex bptr;         // Pointer to curve B in (u,v) parameter space
    DEIndex cptr;         // Pointer to curve C in model space
    int pref = 0;         // Preferred representation: 0=unspecified,
                          //   1=S∘B, 2=C, 3=equally preferred
};

std::expected<CurveOnParametricSurfaceEntity, Diagnostic>
parse_curve_on_surface_entity(ParamTokenizer& tok);

} // namespace iges
