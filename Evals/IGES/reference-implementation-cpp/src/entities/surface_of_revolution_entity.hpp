#pragma once
// iges::SurfaceOfRevolutionEntity — Type 120.
//
// §4.18: "A surface of revolution is defined by an axis of rotation
//   (which shall be a Line Entity), a generatrix, and start and
//   terminate rotation angles."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct SurfaceOfRevolutionEntity {
    DEIndex l;                // Pointer to Line Entity (axis of revolution)
    DEIndex c;                // Pointer to generatrix entity
    Real sa = 0.0;            // Start angle in radians
    Real ta = 0.0;            // Terminate angle in radians
};

std::expected<SurfaceOfRevolutionEntity, Diagnostic>
parse_surface_of_revolution_entity(ParamTokenizer& tok);

} // namespace iges
