#pragma once
// iges::RightCircularCylinderEntity — Type 154.
//
// §4.39: "The right circular cylinder is defined by the center of
//   one circular cylinder face, a unit vector, a height, and a radius."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>

namespace iges {

struct RightCircularCylinderEntity {
    Real h = 0.0;                  // Height
    Real r = 0.0;                  // Radius
    Vec3 face_center = {0, 0, 0};  // First face center
    Vec3 axis = {0, 0, 1};        // Axis direction
};

std::expected<RightCircularCylinderEntity, Diagnostic>
parse_right_circular_cylinder_entity(ParamTokenizer& tok);

} // namespace iges
