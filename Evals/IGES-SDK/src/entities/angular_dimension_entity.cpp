// iges::AngularDimensionEntity — Full implementation.

#include "angular_dimension_entity.hpp"

namespace iges {

std::expected<AngularDimensionEntity, Diagnostic>
parse_angular_dimension_entity(ParamTokenizer& tok) {
    AngularDimensionEntity e;

    auto n = tok.next_pointer(); if (!n) return std::unexpected(n.error()); e.denote = *n;
    auto w1 = tok.next_pointer(); if (!w1) return std::unexpected(w1.error()); e.dewit1 = *w1;
    auto w2 = tok.next_pointer(); if (!w2) return std::unexpected(w2.error()); e.dewit2 = *w2;
    auto xt = tok.next_real(); if (!xt) return std::unexpected(xt.error()); e.xt = *xt;
    auto yt = tok.next_real(); if (!yt) return std::unexpected(yt.error()); e.yt = *yt;
    auto r = tok.next_real(); if (!r) return std::unexpected(r.error()); e.radius = *r;
    auto a1 = tok.next_pointer(); if (!a1) return std::unexpected(a1.error()); e.dearrw1 = *a1;
    auto a2 = tok.next_pointer(); if (!a2) return std::unexpected(a2.error()); e.dearrw2 = *a2;

    return e;
}

} // namespace iges
