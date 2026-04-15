#pragma once
// iges::CompositeCurveEntity — Type 102.

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct CompositeCurveEntity {
    std::vector<DEIndex> constituents;  // pointers to constituent entity DEs
};

std::expected<CompositeCurveEntity, Diagnostic>
parse_composite_curve_entity(ParamTokenizer& tok);

} // namespace iges
