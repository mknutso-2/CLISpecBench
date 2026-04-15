#pragma once
// iges::TextDisplayTemplateEntity — Type 312.
//
// §4.75: "The Text Display Template Entity specifies the parameters
//   for the display of text strings."
// Forms 0 (absolute) and 1 (incremental).

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct TextDisplayTemplateEntity {
    Real cbw = 0.0;   // Character box width
    Real cbh = 0.0;   // Character box height
    int fc = 0;       // Font code (or negative pointer to Type 310)
    Real sl = 0.0;    // Slant angle of text in radians (pi/2 = no slant)
    Real a = 0.0;     // Rotation angle in radians
    int m = 0;        // Mirror flag: 0=none, 1=perpendicular to base, 2=about base
    int vh = 0;       // Rotate internal text flag: 0=horizontal, 1=vertical
    Real xs = 0.0;    // X of start (Form 0) or X increment (Form 1)
    Real ys = 0.0;    // Y of start (Form 0) or Y increment (Form 1)
    Real zs = 0.0;    // Z of start (Form 0) or Z increment (Form 1)
};

std::expected<TextDisplayTemplateEntity, Diagnostic>
parse_text_display_template_entity(ParamTokenizer& tok);

} // namespace iges
