#pragma once
// iges::OffsetSurfaceEntity — Type 140.
//
// §4.30: "The offset surface is a surface defined in terms of an
//   existing surface."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct OffsetSurfaceEntity {
    Real nx = 0.0;            // Offset indicator X component
    Real ny = 0.0;            // Offset indicator Y component
    Real nz = 0.0;            // Offset indicator Z component
    Real d = 0.0;             // Offset distance
    DEIndex de;               // Pointer to surface entity to be offset
};

std::expected<OffsetSurfaceEntity, Diagnostic>
parse_offset_surface_entity(ParamTokenizer& tok);

} // namespace iges
