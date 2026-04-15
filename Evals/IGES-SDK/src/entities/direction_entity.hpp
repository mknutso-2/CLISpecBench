#pragma once
// iges::DirectionEntity — Type 123.

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct DirectionEntity {
    Real x = 0.0;  // Direction ratio w.r.t. X axis
    Real y = 0.0;  // Direction ratio w.r.t. Y axis
    Real z = 0.0;  // Direction ratio w.r.t. Z axis
};

std::expected<DirectionEntity, Diagnostic>
parse_direction_entity(ParamTokenizer& tok);

} // namespace iges
