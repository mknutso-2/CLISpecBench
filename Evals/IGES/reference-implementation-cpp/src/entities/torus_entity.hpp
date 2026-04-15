#pragma once
// iges::TorusEntity — Type 160.
//
// §4.42: "The torus is the solid formed by revolving a circular disc
//   about a specified coplanar axis."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>

namespace iges {

struct TorusEntity {
    Real r1 = 0.0;             // Major radius (axis to disc center)
    Real r2 = 0.0;             // Minor radius (disc radius)
    Vec3 center = {0, 0, 0};
    Vec3 axis = {0, 0, 1};
};

std::expected<TorusEntity, Diagnostic>
parse_torus_entity(ParamTokenizer& tok);

} // namespace iges
