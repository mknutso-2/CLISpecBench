#pragma once
// iges::NodalLoadConstraintEntity — Type 418.
//
// §4.139: "This entity relates loads or constraints to specific
//   nodes in the Finite Element Model."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct NodalLoadConstraintEntity {
    int nc = 0;                        // Total number of cases
    int type = 0;                      // 1 = Loads, 2 = Constraints
    DEIndex de{0};                     // Pointer to Node
    std::vector<DEIndex> ptrs;         // Pointers to Tabular Data Properties
};

std::expected<NodalLoadConstraintEntity, Diagnostic>
parse_nodal_load_constraint_entity(ParamTokenizer& tok);

} // namespace iges
