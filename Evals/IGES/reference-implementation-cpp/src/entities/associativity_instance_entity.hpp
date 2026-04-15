#pragma once
// iges::AssociativityInstanceEntity — Type 402.
//
// §4.90: "The Associativity Instance Entity defines an occurrence
//   of a given Associativity." Form 1 = Group Associativity.

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct AssociativityInstanceEntity {
    int n = 0;
    std::vector<DEIndex> entries;
};

std::expected<AssociativityInstanceEntity, Diagnostic>
parse_associativity_instance_entity(ParamTokenizer& tok);

} // namespace iges
