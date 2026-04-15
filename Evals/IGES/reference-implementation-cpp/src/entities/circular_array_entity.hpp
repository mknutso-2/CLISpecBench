#pragma once
// iges::CircularArrayEntity — Type 414.
//
// §4.137: "A Circular Array Subfigure Instance Entity produces
//   copies of a defined subfigure in a circular pattern."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>
#include <vector>

namespace iges {

struct CircularArrayEntity {
    DEIndex de;                     // 1: Pointer to base entity DE
    int ne = 0;                     // 2: Total number of possible instance locations
    Vec3 center;                    // 3-5: Center of imaginary circle X, Y, Z
    Real r = 0.0;                   // 6: Radius of imaginary circle
    Real as = 0.0;                  // 7: Start angle in radians
    Real ad = 0.0;                  // 8: Delta angle in radians
    int lc = 0;                     // 9: DO-DON'T list count (0=display all)
    int ddf = 0;                    // 10: DO-DON'T flag (0=DO, 1=DON'T)
    std::vector<int> positions;     // 11..10+LC: Position numbers
};

std::expected<CircularArrayEntity, Diagnostic>
parse_circular_array_entity(ParamTokenizer& tok);

} // namespace iges
