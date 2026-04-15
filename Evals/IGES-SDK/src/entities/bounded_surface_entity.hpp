#pragma once
// iges::BoundedSurfaceEntity — Type 143.
//
// §4.33: "The Bounded Surface Entity (Type 143) is used to
//   represent trimmed surfaces."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct BoundedSurfaceEntity {
    int type = 0;                   // 0 = model space only, 1 = model + parameter space
    DEIndex sptr;                   // Pointer to untrimmed surface
    int n = 0;                      // Number of boundary entities
    std::vector<DEIndex> bdpt;      // Pointers to Boundary entities (Type 141)
};

std::expected<BoundedSurfaceEntity, Diagnostic>
parse_bounded_surface_entity(ParamTokenizer& tok);

} // namespace iges
