// iges::RectangularArrayEntity — Full implementation.

#include "rectangular_array_entity.hpp"

namespace iges {

std::expected<RectangularArrayEntity, Diagnostic>
parse_rectangular_array_entity(ParamTokenizer& tok) {
    RectangularArrayEntity e;

    auto de = tok.next_pointer(); if (!de) return std::unexpected(de.error()); e.de = *de;
    auto s = tok.next_real_or(1.0); if (!s) return std::unexpected(s.error()); e.s = *s;
    auto x = tok.next_real(); if (!x) return std::unexpected(x.error()); e.position.x = *x;
    auto y = tok.next_real(); if (!y) return std::unexpected(y.error()); e.position.y = *y;
    auto z = tok.next_real(); if (!z) return std::unexpected(z.error()); e.position.z = *z;
    auto nc = tok.next_integer(); if (!nc) return std::unexpected(nc.error()); e.nc = *nc;
    auto nr = tok.next_integer(); if (!nr) return std::unexpected(nr.error()); e.nr = *nr;
    auto dx = tok.next_real(); if (!dx) return std::unexpected(dx.error()); e.dx = *dx;
    auto dy = tok.next_real(); if (!dy) return std::unexpected(dy.error()); e.dy = *dy;
    auto ax = tok.next_real(); if (!ax) return std::unexpected(ax.error()); e.ax = *ax;
    auto lc = tok.next_integer(); if (!lc) return std::unexpected(lc.error()); e.lc = *lc;
    auto ddf = tok.next_integer(); if (!ddf) return std::unexpected(ddf.error()); e.ddf = *ddf;

    e.positions.reserve(e.lc);
    for (int i = 0; i < e.lc; ++i) {
        auto p = tok.next_integer(); if (!p) return std::unexpected(p.error());
        e.positions.push_back(*p);
    }

    return e;
}

} // namespace iges
