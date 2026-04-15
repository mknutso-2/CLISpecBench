// iges::CircularArcEntity — Full implementation.

#include "circular_arc_entity.hpp"
#include <cmath>
#include <numbers>

namespace iges {

Real CircularArcEntity::radius() const {
    Real dx = x2 - x1;
    Real dy = y2 - y1;
    return std::sqrt(dx*dx + dy*dy);
}

Real CircularArcEntity::start_angle() const {
    return std::atan2(y2 - y1, x2 - x1);
}

Real CircularArcEntity::terminate_angle() const {
    Real a = std::atan2(y3 - y1, x3 - x1);
    Real s = start_angle();
    // Ensure 0 <= t3 - t2 <= 2*pi per spec
    while (a < s) a += 2.0 * std::numbers::pi;
    return a;
}

bool CircularArcEntity::is_full_circle() const {
    return (x2 == x3) && (y2 == y3);
}

Vec3 CircularArcEntity::evaluate(Real t) const {
    Real r = radius();
    return {x1 + r * std::cos(t),
            y1 + r * std::sin(t),
            zt};
}

std::expected<CircularArcEntity, Diagnostic>
parse_circular_arc_entity(ParamTokenizer& tok) {
    CircularArcEntity e;

    auto zt_v = tok.next_real();
    if (!zt_v) return std::unexpected(zt_v.error());
    e.zt = *zt_v;

    auto cx = tok.next_real();
    if (!cx) return std::unexpected(cx.error());
    e.x1 = *cx;

    auto cy = tok.next_real();
    if (!cy) return std::unexpected(cy.error());
    e.y1 = *cy;

    auto sx = tok.next_real();
    if (!sx) return std::unexpected(sx.error());
    e.x2 = *sx;

    auto sy = tok.next_real();
    if (!sy) return std::unexpected(sy.error());
    e.y2 = *sy;

    auto tx = tok.next_real();
    if (!tx) return std::unexpected(tx.error());
    e.x3 = *tx;

    auto ty = tok.next_real();
    if (!ty) return std::unexpected(ty.error());
    e.y3 = *ty;

    return e;
}

} // namespace iges
