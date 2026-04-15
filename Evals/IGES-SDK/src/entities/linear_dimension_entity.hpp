#pragma once
// iges::LinearDimensionEntity — Type 216.
//
// §4.60: "A Linear Dimension Entity consists of a general note,
//   two leaders, and zero, one, or two witness lines."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct LinearDimensionEntity {
    DEIndex denote;
    DEIndex dearrw1;
    DEIndex dearrw2;
    DEIndex dewit1;
    DEIndex dewit2;
};

std::expected<LinearDimensionEntity, Diagnostic>
parse_linear_dimension_entity(ParamTokenizer& tok);

} // namespace iges
