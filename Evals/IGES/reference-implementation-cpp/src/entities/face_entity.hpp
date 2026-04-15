#pragma once
// iges::FaceEntity — Type 510, Form 1.
//
// §4.146: "The Face Entity is a bound (partial) of R^3 which has
//   finite area."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct FaceEntity {
    DEIndex surf;              // Underlying surface pointer
    int n = 0;                 // Number of loops
    bool outer_loop_flag = false;
    std::vector<DEIndex> loops;
};

std::expected<FaceEntity, Diagnostic>
parse_face_entity(ParamTokenizer& tok);

} // namespace iges
