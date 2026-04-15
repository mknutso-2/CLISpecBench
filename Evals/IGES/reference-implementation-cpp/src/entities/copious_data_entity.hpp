#pragma once
// iges::CopiousDataEntity — Type 106.
//
// §4.5: "A Copious Data Entity stores collections of points
//   and optionally associated vectors."
//   Form 1-3: coordinate data; Form 11-13: linear path;
//   Form 40: witness line; Form 63: simple closed area.

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct CopiousDataEntity {
    int ip = 0;         // interpretation flag: 1=2D, 2=3D, 3=3D+vector
    int n = 0;          // number of tuples
    Real zt = 0.0;      // common z displacement (IP=1 only)
    std::vector<Real> data;  // flat array: N*2, N*3, or N*6 values

    // Path evaluation for forms 11 (2D), 12 (3D), and 63 (closed 2D).
    // Parameter t ∈ [0, n−1]: integer values land on tuple points,
    // fractional values linearly interpolate between tuples i and i+1.
    // Values outside the domain are clamped to the endpoints.
    Vec3 evaluate(Real t) const;

    // Returns the k-th tuple's point component as (x, y, z), accounting
    // for the interpretation flag (ip=1 supplies zt for z).
    Vec3 point_at(int k) const;
};

std::expected<CopiousDataEntity, Diagnostic>
parse_copious_data_entity(ParamTokenizer& tok);

} // namespace iges
