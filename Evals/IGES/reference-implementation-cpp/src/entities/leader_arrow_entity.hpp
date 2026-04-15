#pragma once
// iges::LeaderArrowEntity — Type 214.
//
// §4.62: "A Leader (Arrow) Entity consists of an arrowhead
//   and one or more line segments."
// Arrowhead style is conveyed via DE Form Number (1-12).

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>
#include <vector>

namespace iges {

struct LeaderSegment {
    Real x = 0.0;
    Real y = 0.0;
};

struct LeaderArrowEntity {
    int n = 0;
    Real ad1 = 0.0;     // Arrowhead height
    Real ad2 = 0.0;     // Arrowhead width
    Real zt = 0.0;      // Z depth
    Real xh = 0.0;      // Arrowhead coordinate X
    Real yh = 0.0;      // Arrowhead coordinate Y
    std::vector<LeaderSegment> segments;
};

std::expected<LeaderArrowEntity, Diagnostic>
parse_leader_arrow_entity(ParamTokenizer& tok);

} // namespace iges
