// iges::TransformationMatrixEntity — Full implementation.

#include "transformation_matrix_entity.hpp"

namespace iges {

Vec3 TransformationMatrixEntity::apply(Vec3 const& p) const {
    return rotation * p + translation;
}

TransformationMatrixEntity TransformationMatrixEntity::compose(
    TransformationMatrixEntity const& other) const {
    // this applied after other: R = this.R * other.R, T = this.R * other.T + this.T
    TransformationMatrixEntity result;
    result.rotation = multiply(rotation, other.rotation);
    result.translation = rotation * other.translation + translation;
    return result;
}

std::expected<TransformationMatrixEntity, Diagnostic>
parse_transformation_matrix_entity(ParamTokenizer& tok) {
    TransformationMatrixEntity e;

    // 12 reals: R11,R12,R13,T1, R21,R22,R23,T2, R31,R32,R33,T3
    for (int row = 0; row < 3; ++row) {
        for (int col = 0; col < 3; ++col) {
            auto v = tok.next_real();
            if (!v) return std::unexpected(v.error());
            e.rotation(row, col) = *v;
        }
        auto t = tok.next_real();
        if (!t) return std::unexpected(t.error());
        if (row == 0) e.translation.x = *t;
        else if (row == 1) e.translation.y = *t;
        else e.translation.z = *t;
    }

    return e;
}

} // namespace iges
