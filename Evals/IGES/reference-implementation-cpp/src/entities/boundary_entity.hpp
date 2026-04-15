#pragma once
// iges::BoundaryEntity — Type 141.
//
// §4.31: "Each Boundary Entity identifies a surface boundary
//   consisting of a set of curves lying on the surface."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct BoundaryCurve {
    DEIndex crvpt;                     // Model space curve pointer
    int sense = 0;                     // 1=no reversal, 2=reversed
    int k = 0;                         // Number of param space curves
    std::vector<DEIndex> pscpt;        // Parameter space curve pointers
};

struct BoundaryEntity {
    int type = 0;                      // 0=model space only, 1=model+param
    int pref = 0;                      // Preferred representation
    DEIndex sptr;                      // Pointer to untrimmed surface
    int n = 0;                         // Number of curves
    std::vector<BoundaryCurve> curves;
};

std::expected<BoundaryEntity, Diagnostic>
parse_boundary_entity(ParamTokenizer& tok);

} // namespace iges
