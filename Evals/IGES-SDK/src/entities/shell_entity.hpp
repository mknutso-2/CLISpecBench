#pragma once
// iges::ShellEntity — Type 514.
//
// §4.147: "The shell is represented as a set of edge-connected,
//   oriented uses of faces."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct FaceUse {
    DEIndex face;
    bool orientation = true;
};

struct ShellEntity {
    int n = 0;
    std::vector<FaceUse> faces;
};

std::expected<ShellEntity, Diagnostic>
parse_shell_entity(ParamTokenizer& tok);

} // namespace iges
