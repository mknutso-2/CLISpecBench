// iges::CurveDimensionEntity — Full implementation.

#include "curve_dimension_entity.hpp"

namespace iges {

std::expected<CurveDimensionEntity, Diagnostic>
parse_curve_dimension_entity(ParamTokenizer& tok) {
    CurveDimensionEntity e;

    auto n = tok.next_pointer(); if (!n) return std::unexpected(n.error()); e.denote = *n;
    auto c1 = tok.next_pointer(); if (!c1) return std::unexpected(c1.error()); e.decurv1 = *c1;
    auto c2 = tok.next_pointer(); if (!c2) return std::unexpected(c2.error()); e.decurv2 = *c2;
    auto a1 = tok.next_pointer(); if (!a1) return std::unexpected(a1.error()); e.dearr1 = *a1;
    auto a2 = tok.next_pointer(); if (!a2) return std::unexpected(a2.error()); e.dearr2 = *a2;
    auto w1 = tok.next_pointer(); if (!w1) return std::unexpected(w1.error()); e.dewit1 = *w1;
    auto w2 = tok.next_pointer(); if (!w2) return std::unexpected(w2.error()); e.dewit2 = *w2;

    return e;
}

} // namespace iges
