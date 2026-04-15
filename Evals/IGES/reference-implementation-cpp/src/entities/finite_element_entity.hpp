#pragma once
// iges::FiniteElementEntity — Type 136.
//
// §4.28: "A finite element defined by an element topology (node connectivity),
// along with physical and material properties."
// Parameters: ITOP, N, DE(1)..DE(N), ETYP

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct FiniteElementEntity {
    int itop = 0;                   // Topology type (1-38, 5001=implementor-defined)
    int n = 0;                      // Number of nodes defining element
    std::vector<DEIndex> nodes;     // Pointers to Node entities (Type 134)
    std::string etyp;               // Element type name (e.g., "BEAM", "LTRIA")
};

std::expected<FiniteElementEntity, Diagnostic>
parse_finite_element_entity(ParamTokenizer& tok);

} // namespace iges
