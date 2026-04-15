#pragma once
// iges::NetworkSubfigureDefinitionEntity — Type 320.
//
// §4.78: "A Network Subfigure Definition Entity permits a single
//   definition ... to be utilized in multiple instances in the
//   network schematic."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <string>
#include <vector>

namespace iges {

struct NetworkSubfigureDefinitionEntity {
    int depth = 0;                     // Depth of subfigure nesting
    std::string name;                  // Subfigure name
    int na = 0;                        // Number of associated entities
    std::vector<DEIndex> associated;   // Associated entity pointers
    int tf = 0;                        // Type flag: 0=not specified, 1=logical, 2=physical
    std::string prd;                   // Primary reference designator
    DEIndex dptr{0};                   // Pointer to Text Display Template DE
    int nc = 0;                        // Number of connect points
    std::vector<DEIndex> connects;     // Connect point pointers (or zero)
};

std::expected<NetworkSubfigureDefinitionEntity, Diagnostic>
parse_network_subfigure_definition_entity(ParamTokenizer& tok);

} // namespace iges
