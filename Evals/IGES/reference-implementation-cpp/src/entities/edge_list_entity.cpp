// iges::EdgeListEntity — Full implementation.

#include "edge_list_entity.hpp"

namespace iges {

std::expected<EdgeListEntity, Diagnostic>
parse_edge_list_entity(ParamTokenizer& tok) {
    EdgeListEntity e;

    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.n = *n;

    e.edges.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        EdgeTuple et;
        auto curv = tok.next_pointer(); if (!curv) return std::unexpected(curv.error()); et.curve = *curv;
        auto svp = tok.next_pointer(); if (!svp) return std::unexpected(svp.error()); et.svp = *svp;
        auto sv = tok.next_integer(); if (!sv) return std::unexpected(sv.error()); et.sv = *sv;
        auto tvp = tok.next_pointer(); if (!tvp) return std::unexpected(tvp.error()); et.tvp = *tvp;
        auto tv = tok.next_integer(); if (!tv) return std::unexpected(tv.error()); et.tv = *tv;
        e.edges.push_back(et);
    }

    return e;
}

} // namespace iges
