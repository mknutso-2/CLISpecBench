#pragma once
// iges::EllipsoidEntity — Type 168.
//
// §4.45: "The ellipsoid is a solid bounded by the surface defined by
//   X^2/LX^2 + Y^2/LY^2 + Z^2/LZ^2 = 1."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>

namespace iges {

struct EllipsoidEntity {
    Real lx = 0.0, ly = 0.0, lz = 0.0;  // Semi-axis lengths
    Vec3 center = {0, 0, 0};
    Vec3 x_axis = {1, 0, 0};             // Local X (major)
    Vec3 z_axis = {0, 0, 1};             // Local Z (minor)
};

std::expected<EllipsoidEntity, Diagnostic>
parse_ellipsoid_entity(ParamTokenizer& tok);

} // namespace iges
