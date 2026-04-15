#pragma once
// iges::MSBOEntity — Type 186 (Manifold Solid B-Rep Object).
//
// §4.49: "The MSBO defines a manifold solid by enumerating its boundary."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct VoidShell {
    DEIndex shell;
    bool orientation = true;
};

struct MSBOEntity {
    DEIndex shell;             // Outer shell pointer
    bool sof = true;           // Shell orientation flag
    int n = 0;                 // Number of void shells
    std::vector<VoidShell> voids;
};

std::expected<MSBOEntity, Diagnostic>
parse_msbo_entity(ParamTokenizer& tok);

} // namespace iges
