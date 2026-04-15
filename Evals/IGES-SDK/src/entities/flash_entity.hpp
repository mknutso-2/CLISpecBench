#pragma once
// iges::FlashEntity — Type 125.
//
// §4.22: "A Flash Entity is a point in the ZT=0 plane that defines
//   the location of a specific instance of a particular closed area."
//   Form 0: defined by referenced entity
//   Form 1: Circular (DIM1=diameter)
//   Form 2: Rectangle (DIM1=X length, DIM2=Y length)
//   Form 3: Donut
//   Form 4: Canoe

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct FlashEntity {
    Real x = 0.0;       // X reference of flash
    Real y = 0.0;       // Y reference of flash
    Real dim1 = 0.0;    // First flash sizing parameter
    Real dim2 = 0.0;    // Second flash sizing parameter
    Real rot = 0.0;     // Rotation about reference point in radians
    DEIndex de;         // Pointer to DE of referenced entity or zero
};

std::expected<FlashEntity, Diagnostic>
parse_flash_entity(ParamTokenizer& tok);

} // namespace iges
