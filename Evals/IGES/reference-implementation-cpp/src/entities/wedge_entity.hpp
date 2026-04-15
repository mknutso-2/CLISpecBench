#pragma once
// iges::WedgeEntity — Type 152.
//
// §4.38: "The right angular wedge is defined with one vertex at
//   (X1,Y1,Z1) and three orthogonal edges."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>

namespace iges {

struct WedgeEntity {
    Real lx = 0.0, ly = 0.0, lz = 0.0;  // Edge lengths
    Real ltx = 0.0;                       // X-length at distance LY
    Vec3 corner = {0, 0, 0};
    Vec3 x_axis = {1, 0, 0};
    Vec3 z_axis = {0, 0, 1};
};

std::expected<WedgeEntity, Diagnostic>
parse_wedge_entity(ParamTokenizer& tok);

} // namespace iges
