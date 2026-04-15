// iges::DiameterDimensionEntity — Full implementation.

#include "diameter_dimension_entity.hpp"

namespace iges {

std::expected<DiameterDimensionEntity, Diagnostic>
parse_diameter_dimension_entity(ParamTokenizer& tok) {
    DiameterDimensionEntity e;

    auto n = tok.next_pointer(); if (!n) return std::unexpected(n.error()); e.denote = *n;
    auto a1 = tok.next_pointer(); if (!a1) return std::unexpected(a1.error()); e.dearrw1 = *a1;
    auto a2 = tok.next_pointer(); if (!a2) return std::unexpected(a2.error()); e.dearrw2 = *a2;
    auto xt = tok.next_real(); if (!xt) return std::unexpected(xt.error()); e.xt = *xt;
    auto yt = tok.next_real(); if (!yt) return std::unexpected(yt.error()); e.yt = *yt;

    return e;
}

} // namespace iges
