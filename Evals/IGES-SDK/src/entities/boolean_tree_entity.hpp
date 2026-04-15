#pragma once
// iges::BooleanTreeEntity — Type 180.
//
// §4.46: "The Boolean tree describes a binary tree structure composed
//   of regularized Boolean operations and operands, in postorder notation."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct BooleanTreeEntity {
    int n = 0;                       // Length of post-order notation
    std::vector<int> entries;        // Positive = operation, negative = pointer
    // Operations: 1=Union, 2=Intersection, 3=Difference
};

std::expected<BooleanTreeEntity, Diagnostic>
parse_boolean_tree_entity(ParamTokenizer& tok);

} // namespace iges
