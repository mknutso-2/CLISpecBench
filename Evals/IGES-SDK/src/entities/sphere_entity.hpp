#pragma once
// iges::SphereEntity — Type 158.
//
// §4.41: "The sphere is defined with its center coordinates at
//   (X1,Y1,Z1) and a radius R."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>

namespace iges {

struct SphereEntity {
    Real radius = 0.0;
    Vec3 center = {0, 0, 0};
};

std::expected<SphereEntity, Diagnostic>
parse_sphere_entity(ParamTokenizer& tok);

} // namespace iges
