#pragma once
// iges::PointDimensionEntity — Type 220.
//
// §4.65: "A Point Dimension Entity consists of a leader (arrow), a
//   general note, and an optional circle or hexagon enclosing
//   the point."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct PointDimensionEntity {
    DEIndex denote;     // Pointer to DE of General Note Entity
    DEIndex dearrw;     // Pointer to DE of leader (arrow)
    DEIndex degeom;     // Pointer to DE of the enclosing geometric entity
};

std::expected<PointDimensionEntity, Diagnostic>
parse_point_dimension_entity(ParamTokenizer& tok);

} // namespace iges
