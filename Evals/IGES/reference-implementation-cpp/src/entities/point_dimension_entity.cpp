// iges::PointDimensionEntity — Full implementation.

#include "point_dimension_entity.hpp"

namespace iges {

std::expected<PointDimensionEntity, Diagnostic>
parse_point_dimension_entity(ParamTokenizer& tok) {
    PointDimensionEntity e;

    auto n = tok.next_pointer(); if (!n) return std::unexpected(n.error()); e.denote = *n;
    auto a = tok.next_pointer(); if (!a) return std::unexpected(a.error()); e.dearrw = *a;
    auto g = tok.next_pointer(); if (!g) return std::unexpected(g.error()); e.degeom = *g;

    return e;
}

} // namespace iges
