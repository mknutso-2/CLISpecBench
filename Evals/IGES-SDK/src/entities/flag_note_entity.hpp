#pragma once
// iges::FlagNoteEntity — Type 208.
//
// §4.58: "A Flag Note Entity is a label entity with a flag (triangular
//   or rectangular) surrounding it."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct FlagNoteEntity {
    Real xt = 0.0;      // X coordinate of lower left corner
    Real yt = 0.0;      // Y coordinate of lower left corner
    Real zt = 0.0;      // Z coordinate of lower left corner
    Real angle = 0.0;   // Rotation angle in radians
    DEIndex denote;     // Pointer to DE of General Note Entity
    int n = 0;          // Number of associated leader arrows
    std::vector<DEIndex> leaders;  // Pointers to DE of leader arrows
};

std::expected<FlagNoteEntity, Diagnostic>
parse_flag_note_entity(ParamTokenizer& tok);

} // namespace iges
