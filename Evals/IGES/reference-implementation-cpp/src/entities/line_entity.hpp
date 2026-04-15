#pragma once
// iges::LineEntity — Type 110, Forms 0/1/2.

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct LineEntity {
    Vec3 start;      // P1
    Vec3 terminate;  // P2

    // Evaluate default parameterization: C(t) = P1 + t*(P2 - P1)
    Vec3 evaluate(Real t) const;
};

std::expected<LineEntity, Diagnostic>
parse_line_entity(ParamTokenizer& tok);

} // namespace iges
