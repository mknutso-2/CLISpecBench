#pragma once
// iges::AssociativityDefinitionEntity — Type 302.
//
// §4.69: Defines the structure of an implementor-defined associativity.
// Parameters: K, {BP(i), OR(i), N(i), IT(i,1..N(i))} x K
//
// Each class specifies: back-pointer requirement, ordering, number of items
// per entry, and the type of each item (1=pointer, 2=value, 3=value-or-pointer).

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct AssociativityClass {
    int bp = 0;                        // 1 = back pointers required, 2 = not required
    int order = 0;                     // 1 = ordered class, 2 = unordered class
    int n = 0;                         // Number of items per entry
    std::vector<int> item_types;       // Type of each item (1=pointer, 2=value, 3=either)
};

struct AssociativityDefinitionEntity {
    int k = 0;                         // Number of class definitions
    std::vector<AssociativityClass> classes;
};

std::expected<AssociativityDefinitionEntity, Diagnostic>
parse_associativity_definition_entity(ParamTokenizer& tok);

} // namespace iges
