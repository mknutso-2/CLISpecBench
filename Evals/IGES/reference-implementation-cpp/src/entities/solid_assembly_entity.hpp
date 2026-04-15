#pragma once
// iges::SolidAssemblyEntity — Type 184.
//
// §4.48: "A solid assembly is a collection of items which possess
//   a shared fixed geometric relationship."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct SolidAssemblyEntity {
    int n = 0;                          // Number of items
    std::vector<DEIndex> items;         // Item pointers
    std::vector<DEIndex> transforms;    // Transform matrix pointers (0=identity)
};

std::expected<SolidAssemblyEntity, Diagnostic>
parse_solid_assembly_entity(ParamTokenizer& tok);

} // namespace iges
