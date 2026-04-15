#pragma once
// iges::NetworkSubfigureInstanceEntity — Type 420.
//
// §4.140: "Each instance of a Network Subfigure Definition Entity
//   (Type 320) is specified by a Network Subfigure Instance Entity."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <string>
#include <vector>

namespace iges {

struct NetworkSubfigureInstanceEntity {
    DEIndex de{0};                     // Pointer to Network Subfigure Definition
    Real x = 0.0;                      // Translation X
    Real y = 0.0;                      // Translation Y
    Real z = 0.0;                      // Translation Z
    Real xs = 1.0;                     // Scale factor X (default 1.0)
    Real ys = 1.0;                     // Scale factor Y (default XS)
    Real zs = 1.0;                     // Scale factor Z (default XS)
    int tf = 0;                        // Type flag: 0=not specified, 1=logical, 2=physical
    std::string prd;                   // Primary reference designator
    DEIndex dptr{0};                   // Pointer to Text Display Template DE
    int nc = 0;                        // Number of connect points
    std::vector<DEIndex> cptrs;        // Connect point pointers (or zero)
};

std::expected<NetworkSubfigureInstanceEntity, Diagnostic>
parse_network_subfigure_instance_entity(ParamTokenizer& tok);

} // namespace iges
