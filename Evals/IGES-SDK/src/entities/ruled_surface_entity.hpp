#pragma once
// iges::RuledSurfaceEntity — Type 118.
//
// §4.17: "A ruled surface is formed by moving a line connecting
//   points of equal relative arc length ... on two parametric curves"

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct RuledSurfaceEntity {
    DEIndex de1;              // Pointer to first curve entity
    DEIndex de2;              // Pointer to second curve entity
    int dirflg = 0;           // 0 = first-to-first, 1 = first-to-last
    int devflg = 0;           // 0 = possibly not developable, 1 = developable
};

std::expected<RuledSurfaceEntity, Diagnostic>
parse_ruled_surface_entity(ParamTokenizer& tok);

} // namespace iges
