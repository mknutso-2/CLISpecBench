#pragma once
// iges::TabulatedCylinderEntity — Type 122.
//
// §4.19: "A tabulated cylinder is a surface formed by moving a line
//   segment called the generatrix parallel to itself along a curve
//   called the directrix."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>

namespace iges {

struct TabulatedCylinderEntity {
    DEIndex de;               // Pointer to directrix curve entity
    Vec3 terminate_point;     // (LX, LY, LZ) terminate point of generatrix
};

std::expected<TabulatedCylinderEntity, Diagnostic>
parse_tabulated_cylinder_entity(ParamTokenizer& tok);

} // namespace iges
