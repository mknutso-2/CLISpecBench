// iges::RightCircularCylinderEntity — Full implementation.

#include "right_circular_cylinder_entity.hpp"

namespace iges {

std::expected<RightCircularCylinderEntity, Diagnostic>
parse_right_circular_cylinder_entity(ParamTokenizer& tok) {
    RightCircularCylinderEntity e;

    auto h = tok.next_real(); if (!h) return std::unexpected(h.error()); e.h = *h;
    auto r = tok.next_real(); if (!r) return std::unexpected(r.error()); e.r = *r;

    auto x1 = tok.next_real_or(0.0); if (!x1) return std::unexpected(x1.error()); e.face_center.x = *x1;
    auto y1 = tok.next_real_or(0.0); if (!y1) return std::unexpected(y1.error()); e.face_center.y = *y1;
    auto z1 = tok.next_real_or(0.0); if (!z1) return std::unexpected(z1.error()); e.face_center.z = *z1;

    auto i1 = tok.next_real_or(0.0); if (!i1) return std::unexpected(i1.error()); e.axis.x = *i1;
    auto j1 = tok.next_real_or(0.0); if (!j1) return std::unexpected(j1.error()); e.axis.y = *j1;
    auto k1 = tok.next_real_or(1.0); if (!k1) return std::unexpected(k1.error()); e.axis.z = *k1;

    return e;
}

} // namespace iges
