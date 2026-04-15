// iges::SectionedAreaEntity — Full implementation.

#include "sectioned_area_entity.hpp"

namespace iges {

std::expected<SectionedAreaEntity, Diagnostic>
parse_sectioned_area_entity(ParamTokenizer& tok) {
    SectionedAreaEntity e;

    auto b = tok.next_pointer(); if (!b) return std::unexpected(b.error()); e.bndp = *b;
    auto p = tok.next_integer(); if (!p) return std::unexpected(p.error()); e.patrn = *p;
    auto xt = tok.next_real(); if (!xt) return std::unexpected(xt.error()); e.xt = *xt;
    auto yt = tok.next_real(); if (!yt) return std::unexpected(yt.error()); e.yt = *yt;
    auto zt = tok.next_real(); if (!zt) return std::unexpected(zt.error()); e.zt = *zt;
    auto d = tok.next_real(); if (!d) return std::unexpected(d.error()); e.dist = *d;
    auto a = tok.next_real(); if (!a) return std::unexpected(a.error()); e.angle = *a;
    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.n = *n;

    e.islands.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        auto de = tok.next_pointer(); if (!de) return std::unexpected(de.error());
        e.islands.push_back(*de);
    }

    return e;
}

} // namespace iges
