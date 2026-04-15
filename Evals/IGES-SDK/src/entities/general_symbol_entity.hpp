#pragma once
// iges::GeneralSymbolEntity — Type 228.
//
// §4.67: "A General Symbol Entity consists of a general note, zero or
//   more geometric entities defining the symbol, and zero or more
//   leader (arrow) entities."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct GeneralSymbolEntity {
    DEIndex denote;                     // Pointer to DE of General Note Entity
    int n = 0;                          // Number of geometric entities
    std::vector<DEIndex> geometries;    // Pointers to DE of geometric entities
    int l = 0;                          // Number of leader (arrow) entities
    std::vector<DEIndex> leaders;       // Pointers to DE of leader entities
};

std::expected<GeneralSymbolEntity, Diagnostic>
parse_general_symbol_entity(ParamTokenizer& tok);

} // namespace iges
