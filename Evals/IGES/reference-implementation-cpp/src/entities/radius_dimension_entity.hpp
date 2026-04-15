#pragma once
// iges::RadiusDimensionEntity — Type 222.
//
// §4.66: Form 0 — "Parameters: DENOTE, DEARRW, XT, YT"
//        Form 1 — "Parameters: DENOTE, DEARRW, XT, YT, DEARRW2"

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct RadiusDimensionEntity {
    int form = 0;
    DEIndex denote;             // 1: Pointer to General Note DE
    DEIndex dearrw;             // 2: Pointer to Leader (arrow) DE
    Real xt = 0.0;              // 3: Arc center X
    Real yt = 0.0;              // 4: Arc center Y
    DEIndex dearrw2;            // 5 (Form 1 only): Pointer to second Leader DE
};

std::expected<RadiusDimensionEntity, Diagnostic>
parse_radius_dimension_entity(ParamTokenizer& tok, int form = 0);

} // namespace iges
