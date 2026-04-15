#pragma once
// iges::TextFontDefinitionEntity — Type 310.
//
// §4.74: Defines the appearance of characters in a text font.
// Each character is defined by pen motions on an integer grid.
//
// Parameters: FC, FNAME, SF, SCALE, N,
//   {AC(i), NX(i), NY(i), NM(i), {PF(i,j), X(i,j), Y(i,j)} x NM(i)} x N

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>
#include <string>

namespace iges {

struct PenMotion {
    int pf = 0;                        // Pen up/down flag: 0 = down, 1 = up
    int x = 0;                         // Grid X location
    int y = 0;                         // Grid Y location
};

struct CharacterDefinition {
    int ac = 0;                        // ASCII code
    int nx = 0;                        // Grid X of next character origin
    int ny = 0;                        // Grid Y of next character origin
    int nm = 0;                        // Number of pen motions
    std::vector<PenMotion> motions;
};

struct TextFontDefinitionEntity {
    int fc = 0;                        // Font Code
    std::string fname;                 // Font Name
    int sf = 0;                        // Supersedes Font (number or negated DE pointer)
    int scale = 0;                     // Grid units per text height unit
    int n = 0;                         // Number of characters
    std::vector<CharacterDefinition> characters;
};

std::expected<TextFontDefinitionEntity, Diagnostic>
parse_text_font_definition_entity(ParamTokenizer& tok);

} // namespace iges
