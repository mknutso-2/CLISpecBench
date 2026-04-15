// iges::LineEntity — Full implementation.

#include "line_entity.hpp"

namespace iges {

Vec3 LineEntity::evaluate(Real t) const {
    return start + (terminate - start) * t;
}

std::expected<LineEntity, Diagnostic>
parse_line_entity(ParamTokenizer& tok) {
    LineEntity e;

    auto x1 = tok.next_real();
    if (!x1) return std::unexpected(x1.error());
    e.start.x = *x1;

    auto y1 = tok.next_real();
    if (!y1) return std::unexpected(y1.error());
    e.start.y = *y1;

    auto z1 = tok.next_real();
    if (!z1) return std::unexpected(z1.error());
    e.start.z = *z1;

    auto x2 = tok.next_real();
    if (!x2) return std::unexpected(x2.error());
    e.terminate.x = *x2;

    auto y2 = tok.next_real();
    if (!y2) return std::unexpected(y2.error());
    e.terminate.y = *y2;

    auto z2 = tok.next_real();
    if (!z2) return std::unexpected(z2.error());
    e.terminate.z = *z2;

    return e;
}

} // namespace iges
