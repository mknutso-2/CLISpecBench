#pragma once
// iges::ToroidalSurfaceEntity — Type 198.
//
// §4.54: "The toroidal surface is defined by the center point,
//   the axis direction and the major and minor radii."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct ToroidalSurfaceEntity {
    DEIndex deloc;
    DEIndex deaxis;
    Real majrad = 0.0;
    Real minrad = 0.0;
    DEIndex derefd;            // Reference direction (Form 1 only)
};

std::expected<ToroidalSurfaceEntity, Diagnostic>
parse_toroidal_surface_entity(ParamTokenizer& tok, int form);

} // namespace iges
