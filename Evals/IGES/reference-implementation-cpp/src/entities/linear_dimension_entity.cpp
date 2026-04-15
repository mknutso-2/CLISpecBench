// iges::LinearDimensionEntity — Full implementation.

#include "linear_dimension_entity.hpp"

namespace iges {

std::expected<LinearDimensionEntity, Diagnostic>
parse_linear_dimension_entity(ParamTokenizer& tok) {
    LinearDimensionEntity e;

    auto n = tok.next_pointer(); if (!n) return std::unexpected(n.error()); e.denote = *n;
    auto a1 = tok.next_pointer(); if (!a1) return std::unexpected(a1.error()); e.dearrw1 = *a1;
    auto a2 = tok.next_pointer(); if (!a2) return std::unexpected(a2.error()); e.dearrw2 = *a2;
    auto w1 = tok.next_pointer(); if (!w1) return std::unexpected(w1.error()); e.dewit1 = *w1;
    auto w2 = tok.next_pointer(); if (!w2) return std::unexpected(w2.error()); e.dewit2 = *w2;

    return e;
}

} // namespace iges
