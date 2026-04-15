#pragma once
// iges::OrdinateDimensionEntity — Type 218.
//
// §4.64: Form 0 — "Parameters: DENOTE, DEWIT"
//        Form 1 — "Parameters: DENOTE, DEORD, DESUPP"

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct OrdinateDimensionEntity {
    int form = 0;
    DEIndex denote;             // 1: Pointer to General Note DE
    // Form 0 fields:
    DEIndex dewit;              // 2 (Form 0): Pointer to Witness Line or Leader DE
    // Form 1 fields:
    DEIndex deord;              // 2 (Form 1): Pointer to Leader (ordinate) DE
    DEIndex desupp;             // 3 (Form 1): Pointer to Leader (supplementary) DE
};

std::expected<OrdinateDimensionEntity, Diagnostic>
parse_ordinate_dimension_entity(ParamTokenizer& tok, int form = 0);

} // namespace iges
