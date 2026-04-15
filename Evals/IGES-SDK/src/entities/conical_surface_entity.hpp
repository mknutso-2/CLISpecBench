#pragma once
// iges::ConicalSurfaceEntity — Type 194.
//
// §4.52: "The right circular conical surface is defined by a point
//   on the axis, the axis direction, a radius, and a semi-angle."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct ConicalSurfaceEntity {
    DEIndex deloc;
    DEIndex deaxis;
    Real radius = 0.0;
    Real sangle = 0.0;        // Semi-angle in degrees
    DEIndex derefd;            // Reference direction (Form 1 only)
};

std::expected<ConicalSurfaceEntity, Diagnostic>
parse_conical_surface_entity(ParamTokenizer& tok, int form);

} // namespace iges
