#pragma once
// iges::CurveDimensionEntity — Type 204.
//
// §4.56: "A Curve Dimension Entity consists of a general note, two
//   curves, two leader (arrow) entities, and two witness lines."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct CurveDimensionEntity {
    DEIndex denote;     // Pointer to DE of General Note Entity
    DEIndex decurv1;    // Pointer to DE of first curve
    DEIndex decurv2;    // Pointer to DE of second curve
    DEIndex dearr1;     // Pointer to DE of first leader (arrow)
    DEIndex dearr2;     // Pointer to DE of second leader (arrow)
    DEIndex dewit1;     // Pointer to DE of first witness line
    DEIndex dewit2;     // Pointer to DE of second witness line
};

std::expected<CurveDimensionEntity, Diagnostic>
parse_curve_dimension_entity(ParamTokenizer& tok);

} // namespace iges
