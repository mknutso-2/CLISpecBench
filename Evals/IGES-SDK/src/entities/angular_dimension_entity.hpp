#pragma once
// iges::AngularDimensionEntity — Type 202.
//
// §4.55: "An Angular Dimension Entity consists of a general note,
//   zero or two witness lines, two leaders, and a vertex point."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct AngularDimensionEntity {
    DEIndex denote;
    DEIndex dewit1;
    DEIndex dewit2;
    Real xt = 0.0;
    Real yt = 0.0;
    Real radius = 0.0;
    DEIndex dearrw1;
    DEIndex dearrw2;
};

std::expected<AngularDimensionEntity, Diagnostic>
parse_angular_dimension_entity(ParamTokenizer& tok);

} // namespace iges
