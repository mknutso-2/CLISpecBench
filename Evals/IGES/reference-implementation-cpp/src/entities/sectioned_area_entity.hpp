#pragma once
// iges::SectionedAreaEntity — Type 230.
//
// §4.68: "A Sectioned Area Entity defines a filled region bounded
//   by a closed exterior curve and optionally containing interior
//   island definition curves."
//   Form 0: Standard Crosshatching
//   Form 1: Inverted Crosshatching

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct SectionedAreaEntity {
    DEIndex bndp;           // Pointer to DE of exterior definition curve
    int patrn = 0;          // Fill pattern code (0-19 standard, 20+ extended)
    Real xt = 0.0;          // X coordinate through which a line shall pass
    Real yt = 0.0;          // Y coordinate through which a line shall pass
    Real zt = 0.0;          // Z depth of lines
    Real dist = 0.0;        // Normal distance between adjacent lines
    Real angle = 0.0;       // Angle in radians from XT axis to section lines
    int n = 0;              // Number of island curves or zero
    std::vector<DEIndex> islands;  // Pointers to DE of interior island curves
};

std::expected<SectionedAreaEntity, Diagnostic>
parse_sectioned_area_entity(ParamTokenizer& tok);

} // namespace iges
