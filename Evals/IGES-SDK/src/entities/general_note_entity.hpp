#pragma once
// iges::GeneralNoteEntity — Type 212.
//
// §4.58: "A General Note Entity consists of one or more text strings."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>
#include <string>
#include <vector>

namespace iges {

struct NoteString {
    int nc = 0;
    Real wc = 0.0;
    Real hc = 0.0;
    int fc = 1;
    Real slant = 0.0;
    Real angle = 0.0;
    int mirror = 0;
    int vh = 0;
    Vec3 start;
    std::string text;
};

struct GeneralNoteEntity {
    int ns = 0;
    std::vector<NoteString> strings;
};

std::expected<GeneralNoteEntity, Diagnostic>
parse_general_note_entity(ParamTokenizer& tok);

} // namespace iges
