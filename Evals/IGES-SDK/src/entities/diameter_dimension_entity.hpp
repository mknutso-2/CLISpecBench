#pragma once
// iges::DiameterDimensionEntity — Type 206.
//
// §4.56: "A Diameter Dimension Entity consists of a general note,
//   one or two leaders, and the arc center coordinates."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct DiameterDimensionEntity {
    DEIndex denote;
    DEIndex dearrw1;
    DEIndex dearrw2;
    Real xt = 0.0;
    Real yt = 0.0;
};

std::expected<DiameterDimensionEntity, Diagnostic>
parse_diameter_dimension_entity(ParamTokenizer& tok);

} // namespace iges
