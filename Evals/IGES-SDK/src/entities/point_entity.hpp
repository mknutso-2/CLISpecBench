#pragma once
// iges::PointEntity — Type 116.

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct PointEntity {
    Vec3    coords;
    DEIndex display_symbol;  // 0 = no display symbol
};

std::expected<PointEntity, Diagnostic>
parse_point_entity(ParamTokenizer& tok);

} // namespace iges
