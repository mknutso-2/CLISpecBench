#pragma once
// iges::PlaneSurfaceEntity — Type 190.
//
// §4.50: "The plane surface is defined by a point on the plane
//   and the normal direction to the surface."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct PlaneSurfaceEntity {
    DEIndex deloc;             // Point on surface
    DEIndex denrml;            // Surface normal direction
    DEIndex derefd;            // Reference direction (Form 1 only)
};

std::expected<PlaneSurfaceEntity, Diagnostic>
parse_plane_surface_entity(ParamTokenizer& tok, int form);

} // namespace iges
