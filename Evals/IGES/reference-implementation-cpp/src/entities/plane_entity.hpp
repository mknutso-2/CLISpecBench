#pragma once
// iges::PlaneEntity — Type 108.

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include "../types.hpp"
#include <expected>

namespace iges {

struct PlaneEntity {
    // Plane equation: A*Xt + B*Yt + C*Zt = D
    Real A = 0.0;
    Real B = 0.0;
    Real C = 0.0;
    Real D = 0.0;

    // Pointer to the DE of the closed curve entity (0 for unbounded)
    DEIndex ptr{0};

    // Display symbol location
    Real x = 0.0;
    Real y = 0.0;
    Real z = 0.0;
    Real size = 0.0;  // Size parameter for display symbol
};

std::expected<PlaneEntity, Diagnostic>
parse_plane_entity(ParamTokenizer& tok);

} // namespace iges
