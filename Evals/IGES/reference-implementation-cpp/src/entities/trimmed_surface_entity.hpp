#pragma once
// iges::TrimmedSurfaceEntity — Type 144.
//
// §4.34: "A simple closed curve in the Euclidean plane divides
//   the plane into two disjoint open connected components"

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct TrimmedSurfaceEntity {
    DEIndex pts;                    // Pointer to surface being trimmed
    int n1 = 0;                    // 0 = outer boundary is boundary of D
                                   // 1 = outer boundary specified by PTO
    int n2 = 0;                    // Number of inner boundary curves
    DEIndex pto;                   // Outer boundary (Type 142) or zero
    std::vector<DEIndex> pti;      // Inner boundary pointers (Type 142)
};

std::expected<TrimmedSurfaceEntity, Diagnostic>
parse_trimmed_surface_entity(ParamTokenizer& tok);

} // namespace iges
