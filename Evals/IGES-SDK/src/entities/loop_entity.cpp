// iges::LoopEntity — Full implementation.

#include "loop_entity.hpp"

namespace iges {

std::expected<LoopEntity, Diagnostic>
parse_loop_entity(ParamTokenizer& tok) {
    LoopEntity e;

    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.n = *n;

    e.edge_uses.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        EdgeUse eu;
        auto type = tok.next_integer(); if (!type) return std::unexpected(type.error()); eu.type = *type;
        auto edge = tok.next_pointer(); if (!edge) return std::unexpected(edge.error()); eu.edge = *edge;
        auto ndx = tok.next_integer(); if (!ndx) return std::unexpected(ndx.error()); eu.ndx = *ndx;
        auto of = tok.next_logical(); if (!of) return std::unexpected(of.error()); eu.orientation = *of;
        auto k = tok.next_integer(); if (!k) return std::unexpected(k.error()); eu.k = *k;

        eu.param_curves.reserve(eu.k);
        for (int j = 0; j < eu.k; ++j) {
            ParamSpaceCurve psc;
            auto isop = tok.next_logical(); if (!isop) return std::unexpected(isop.error()); psc.isoparametric = *isop;
            auto curv = tok.next_pointer(); if (!curv) return std::unexpected(curv.error()); psc.curve = *curv;
            eu.param_curves.push_back(psc);
        }

        e.edge_uses.push_back(std::move(eu));
    }

    return e;
}

} // namespace iges
