// iges::CircularArrayEntity — Full implementation.

#include "circular_array_entity.hpp"

namespace iges {

std::expected<CircularArrayEntity, Diagnostic>
parse_circular_array_entity(ParamTokenizer& tok) {
    CircularArrayEntity e;

    auto de = tok.next_pointer(); if (!de) return std::unexpected(de.error()); e.de = *de;
    auto ne = tok.next_integer(); if (!ne) return std::unexpected(ne.error()); e.ne = *ne;
    auto x = tok.next_real(); if (!x) return std::unexpected(x.error()); e.center.x = *x;
    auto y = tok.next_real(); if (!y) return std::unexpected(y.error()); e.center.y = *y;
    auto z = tok.next_real(); if (!z) return std::unexpected(z.error()); e.center.z = *z;
    auto r = tok.next_real(); if (!r) return std::unexpected(r.error()); e.r = *r;
    auto as = tok.next_real(); if (!as) return std::unexpected(as.error()); e.as = *as;
    auto ad = tok.next_real(); if (!ad) return std::unexpected(ad.error()); e.ad = *ad;
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
