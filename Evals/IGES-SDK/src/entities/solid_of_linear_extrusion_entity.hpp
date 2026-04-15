#pragma once
// iges::SolidOfLinearExtrusionEntity — Type 164.
//
// §4.44: "The solid of linear extrusion is defined by translating
//   an area determined by a planar curve."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>

namespace iges {

struct SolidOfLinearExtrusionEntity {
    DEIndex ptr;                    // Pointer to closed curve
    Real length = 0.0;             // Extrusion length
    Vec3 direction = {0, 0, 1};    // Extrusion direction
};

std::expected<SolidOfLinearExtrusionEntity, Diagnostic>
parse_solid_of_linear_extrusion_entity(ParamTokenizer& tok);

} // namespace iges
