#pragma once
// iges::RectangularArrayEntity — Type 412.
//
// §4.136: "A Rectangular Array Subfigure Instance Entity produces
//   copies of a defined subfigure in a rectangular pattern."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>
#include <vector>

namespace iges {

struct RectangularArrayEntity {
    DEIndex de;                     // 1: Pointer to base entity DE
    Real s = 1.0;                   // 2: Scale factor (default 1.0)
    Vec3 position;                  // 3-5: Lower left corner X, Y, Z
    int nc = 0;                     // 6: Number of columns
    int nr = 0;                     // 7: Number of rows
    Real dx = 0.0;                  // 8: Horizontal distance between columns
    Real dy = 0.0;                  // 9: Vertical distance between rows
    Real ax = 0.0;                  // 10: Rotation angle in radians
    int lc = 0;                     // 11: DO-DON'T list count (0=display all)
    int ddf = 0;                    // 12: DO-DON'T flag (0=DO, 1=DON'T)
    std::vector<int> positions;     // 13..12+LC: Position numbers
};

std::expected<RectangularArrayEntity, Diagnostic>
parse_rectangular_array_entity(ParamTokenizer& tok);

} // namespace iges
