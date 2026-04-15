// iges::PointEntity — Full implementation.

#include "point_entity.hpp"

namespace iges {

std::expected<PointEntity, Diagnostic>
parse_point_entity(ParamTokenizer& tok) {
    PointEntity e;

    auto x = tok.next_real();
    if (!x) return std::unexpected(x.error());
    e.coords.x = *x;

    auto y = tok.next_real();
    if (!y) return std::unexpected(y.error());
    e.coords.y = *y;

    auto z = tok.next_real();
    if (!z) return std::unexpected(z.error());
    e.coords.z = *z;

    // PTR is optional — default to 0 (no display symbol)
    auto ptr = tok.next_integer_or(0);
    if (ptr) {
        e.display_symbol = DEIndex{*ptr};
    }

    return e;
}

} // namespace iges
