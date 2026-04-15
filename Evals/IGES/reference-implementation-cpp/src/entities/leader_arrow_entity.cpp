// iges::LeaderArrowEntity — Full implementation.

#include "leader_arrow_entity.hpp"

namespace iges {

std::expected<LeaderArrowEntity, Diagnostic>
parse_leader_arrow_entity(ParamTokenizer& tok) {
    LeaderArrowEntity e;

    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.n = *n;
    auto ad1 = tok.next_real(); if (!ad1) return std::unexpected(ad1.error()); e.ad1 = *ad1;
    auto ad2 = tok.next_real(); if (!ad2) return std::unexpected(ad2.error()); e.ad2 = *ad2;
    auto zt = tok.next_real(); if (!zt) return std::unexpected(zt.error()); e.zt = *zt;
    auto xh = tok.next_real(); if (!xh) return std::unexpected(xh.error()); e.xh = *xh;
    auto yh = tok.next_real(); if (!yh) return std::unexpected(yh.error()); e.yh = *yh;

    e.segments.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        LeaderSegment s;
        auto x = tok.next_real(); if (!x) return std::unexpected(x.error()); s.x = *x;
        auto y = tok.next_real(); if (!y) return std::unexpected(y.error()); s.y = *y;
        e.segments.push_back(s);
    }

    return e;
}

} // namespace iges
