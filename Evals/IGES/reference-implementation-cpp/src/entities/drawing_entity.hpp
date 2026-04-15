#pragma once
// iges::DrawingEntity — Type 404.
//
// §4.96: "The Drawing Entity specifies a drawing as a collection
//   of annotation entities and views."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct DrawingView {
    DEIndex view;
    Real x_origin = 0.0;
    Real y_origin = 0.0;
    Real angle = 0.0;               // Form 1 only: orientation angle in radians
};

struct DrawingEntity {
    int n = 0;
    std::vector<DrawingView> views;
    int m = 0;
    std::vector<DEIndex> annotations;
};

std::expected<DrawingEntity, Diagnostic>
parse_drawing_entity(ParamTokenizer& tok, int form = 0);

} // namespace iges
