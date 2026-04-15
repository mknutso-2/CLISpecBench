#pragma once
// iges::CopiousDataEntity — Type 106.
//
// §4.5: "A Copious Data Entity stores collections of points
//   and optionally associated vectors."
//   Form 1-3: coordinate data; Form 11-13: linear path;
//   Form 40: witness line; Form 63: simple closed area.

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct CopiousDataEntity {
    int ip = 0;         // interpretation flag: 1=2D, 2=3D, 3=3D+vector
    int n = 0;          // number of tuples
    Real zt = 0.0;      // common z displacement (IP=1 only)
    std::vector<Real> data;  // flat array: N*2, N*3, or N*6 values
};

std::expected<CopiousDataEntity, Diagnostic>
parse_copious_data_entity(ParamTokenizer& tok);

} // namespace iges
