// iges::ConeFrustumEntity — Full implementation.

#include "cone_frustum_entity.hpp"

namespace iges {

std::expected<ConeFrustumEntity, Diagnostic>
parse_cone_frustum_entity(ParamTokenizer& tok) {
    ConeFrustumEntity e;

    auto h = tok.next_real(); if (!h) return std::unexpected(h.error()); e.h = *h;
    auto r1 = tok.next_real(); if (!r1) return std::unexpected(r1.error()); e.r1 = *r1;
    auto r2 = tok.next_real_or(0.0); if (!r2) return std::unexpected(r2.error()); e.r2 = *r2;

    auto x1 = tok.next_real_or(0.0); if (!x1) return std::unexpected(x1.error()); e.face_center.x = *x1;
    auto y1 = tok.next_real_or(0.0); if (!y1) return std::unexpected(y1.error()); e.face_center.y = *y1;
    auto z1 = tok.next_real_or(0.0); if (!z1) return std::unexpected(z1.error()); e.face_center.z = *z1;

    auto i1 = tok.next_real_or(0.0); if (!i1) return std::unexpected(i1.error()); e.axis.x = *i1;
    auto j1 = tok.next_real_or(0.0); if (!j1) return std::unexpected(j1.error()); e.axis.y = *j1;
    auto k1 = tok.next_real_or(1.0); if (!k1) return std::unexpected(k1.error()); e.axis.z = *k1;

    return e;
}

} // namespace iges
