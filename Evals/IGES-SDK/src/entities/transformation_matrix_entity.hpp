#pragma once
// iges::TransformationMatrixEntity — Type 124.

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct TransformationMatrixEntity {
    Matrix3x3 rotation;
    Vec3      translation;

    // Apply this transform to a point.
    Vec3 apply(Vec3 const& p) const;

    // Compose: this * other  (apply other first, then this).
    TransformationMatrixEntity compose(TransformationMatrixEntity const& other) const;
};

std::expected<TransformationMatrixEntity, Diagnostic>
parse_transformation_matrix_entity(ParamTokenizer& tok);

} // namespace iges
