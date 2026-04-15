#pragma once
// iges::NodeEntity — Type 134.
//
// §4.27: "A geometric point used in the definition of a finite element."
// Parameters: X/R/R, Y/θ/θ, Z/Z/φ, NDCSP

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct NodeEntity {
    Real x = 0.0;       // First nodal coordinate
    Real y = 0.0;       // Second nodal coordinate
    Real z = 0.0;       // Third nodal coordinate
    DEIndex ndcsp{0};   // Pointer to Transformation Matrix Entity (Form 10/11/12); 0 = Global Cartesian
};

std::expected<NodeEntity, Diagnostic>
parse_node_entity(ParamTokenizer& tok);

} // namespace iges
