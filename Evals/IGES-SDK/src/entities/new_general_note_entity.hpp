#pragma once
// iges::NewGeneralNoteEntity — Type 213.
//
// IGES 5.3, §4.61: "The New General Note Entity accommodates a wider
// range of text characteristics than the General Note Entity (Type 212)."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>
#include <string>
#include <vector>

namespace iges {

struct NewNoteString {
    int fixvar = 0;         // Fixed/Variable width character display
    Real chrwid = 0.0;      // Character width
    Real chrhgt = 0.0;      // Character height
    Real cspace = 0.0;      // Inter-character spacing
    Real lspace = 0.0;      // Interline spacing
    int font = 1;           // Font style
    Real chrang = 0.0;      // Character angle
    std::string cctext;     // Control code string
    int nc = 0;             // Number of characters in TEXT
    Real wt = 0.0;          // Box width
    Real ht = 0.0;          // Box height
    int chrset = 1;         // Character set interpretation
    Real sl = 0.0;          // Slant angle
    Real a = 0.0;           // Rotation angle
    int m = 0;              // Mirror flag (0, 1, 2)
    int vh = 0;             // Rotate internal text flag (0, 1)
    Real xs = 0.0;          // Text start point X
    Real ys = 0.0;          // Text start point Y
    Real zs = 0.0;          // Text start point Z depth
    std::string text;       // Text string
};

struct NewGeneralNoteEntity {
    Real txtcw = 0.0;       // Text containment area width
    Real txtch = 0.0;       // Text containment area height
    int justcd = 0;         // Justification code (0-3)
    Real txtcx = 0.0;       // Text containment area location X
    Real txtcy = 0.0;       // Text containment area location Y
    Real txtcz = 0.0;       // Z depth from TXTCX,TXTCY plane
    Real txtag = 0.0;       // Rotation angle of text containment area
    Real baselx = 0.0;      // Position of first base line X
    Real basely = 0.0;      // Position of first base line Y
    Real baselz = 0.0;      // Z depth from BASELX,BASELY plane
    Real nils = 0.0;        // Normal interline spacing
    int ns = 0;             // Number of text strings
    std::vector<NewNoteString> strings;
};

std::expected<NewGeneralNoteEntity, Diagnostic>
parse_new_general_note_entity(ParamTokenizer& tok);

} // namespace iges
