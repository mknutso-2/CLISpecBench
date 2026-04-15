#pragma once
// iges::SphericalSurfaceEntity — Type 196.
//
// §4.53: "The spherical surface is defined by the center point
//   and the radius."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct SphericalSurfaceEntity {
    DEIndex deloc;             // Center point
    Real radius = 0.0;
    DEIndex deaxis;            // Axis direction (Form 1 only)
    DEIndex derefd;            // Reference direction (Form 1 only)
};

std::expected<SphericalSurfaceEntity, Diagnostic>
parse_spherical_surface_entity(ParamTokenizer& tok, int form);

} // namespace iges
