#pragma once
// iges::SolidOfRevolutionEntity — Type 162.
//
// §4.43: "The Solid of Revolution Entity defines the solid created
//   by revolving the area determined by a planar curve about a
//   specified co-planar axis."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>

namespace iges {

struct SolidOfRevolutionEntity {
    DEIndex ptr;                    // Pointer to curve to be revolved
    Real f = 1.0;                  // Fraction of full rotation
    Vec3 axis_point = {0, 0, 0};   // Point on axis
    Vec3 axis_dir = {0, 0, 1};    // Axis direction
};

std::expected<SolidOfRevolutionEntity, Diagnostic>
parse_solid_of_revolution_entity(ParamTokenizer& tok);

} // namespace iges
