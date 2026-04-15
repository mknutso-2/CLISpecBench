#pragma once
// iges::CylindricalSurfaceEntity — Type 192.
//
// §4.51: "The right circular cylindrical surface is defined by a
//   point on the axis, the direction of the axis, and a radius."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct CylindricalSurfaceEntity {
    DEIndex deloc;             // Point on axis
    DEIndex deaxis;            // Axis direction
    Real radius = 0.0;
    DEIndex derefd;            // Reference direction (Form 1 only)
};

std::expected<CylindricalSurfaceEntity, Diagnostic>
parse_cylindrical_surface_entity(ParamTokenizer& tok, int form);

} // namespace iges
