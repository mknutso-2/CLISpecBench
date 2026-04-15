#pragma once
// iges::ConeFrustumEntity — Type 156.
//
// §4.40: "The right circular cone frustum is defined by the center
//   of the larger circular face."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>

namespace iges {

struct ConeFrustumEntity {
    Real h = 0.0;                  // Height
    Real r1 = 0.0;                 // Larger face radius
    Real r2 = 0.0;                 // Smaller face radius (0 for apex)
    Vec3 face_center = {0, 0, 0};  // Larger face center
    Vec3 axis = {0, 0, 1};        // Axis direction
};

std::expected<ConeFrustumEntity, Diagnostic>
parse_cone_frustum_entity(ParamTokenizer& tok);

} // namespace iges
