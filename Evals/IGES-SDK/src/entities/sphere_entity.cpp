// iges::SphereEntity — Full implementation.

#include "sphere_entity.hpp"

namespace iges {

std::expected<SphereEntity, Diagnostic>
parse_sphere_entity(ParamTokenizer& tok) {
    SphereEntity e;

    auto r = tok.next_real(); if (!r) return std::unexpected(r.error()); e.radius = *r;

    auto x1 = tok.next_real_or(0.0); if (!x1) return std::unexpected(x1.error()); e.center.x = *x1;
    auto y1 = tok.next_real_or(0.0); if (!y1) return std::unexpected(y1.error()); e.center.y = *y1;
    auto z1 = tok.next_real_or(0.0); if (!z1) return std::unexpected(z1.error()); e.center.z = *z1;

    return e;
}

} // namespace iges
