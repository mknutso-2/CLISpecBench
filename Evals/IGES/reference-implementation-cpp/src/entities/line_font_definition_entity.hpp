#pragma once
// iges::LineFontDefinitionEntity — Type 304.
//
// §4.70: Line font specified by a repeating template subfigure (Form 1)
//        or a repeating visible-blank pattern (Form 2).

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <string>
#include <vector>

namespace iges {

struct LineFontDefinitionEntity {
    int form = 0;

    // Form 1 fields (template subfigure):
    int m = 0;              // Display flag (0=align with axes, 1=align with tangent)
    DEIndex l1;             // Pointer to Subfigure Definition Entity
    Real l2 = 0.0;          // Common arc length distance between displays
    Real l3 = 0.0;          // Scale factor

    // Form 2 fields (visible-blank pattern):
    // m = number of segments
    std::vector<Real> segments;  // M segment lengths
    std::string bitmask;         // Hex bitmask: which segments are visible/blank
};

std::expected<LineFontDefinitionEntity, Diagnostic>
parse_line_font_definition_entity(ParamTokenizer& tok, int form);

} // namespace iges
