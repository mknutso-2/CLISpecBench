// iges::RadiusDimensionEntity — Full implementation.

#include "radius_dimension_entity.hpp"

namespace iges {

std::expected<RadiusDimensionEntity, Diagnostic>
parse_radius_dimension_entity(ParamTokenizer& tok, int form) {
    RadiusDimensionEntity e;
    e.form = form;

    auto n = tok.next_pointer(); if (!n) return std::unexpected(n.error()); e.denote = *n;
    auto a = tok.next_pointer(); if (!a) return std::unexpected(a.error()); e.dearrw = *a;
    auto xt = tok.next_real(); if (!xt) return std::unexpected(xt.error()); e.xt = *xt;
    auto yt = tok.next_real(); if (!yt) return std::unexpected(yt.error()); e.yt = *yt;

    if (form == 1) {
        auto a2 = tok.next_pointer(); if (!a2) return std::unexpected(a2.error()); e.dearrw2 = *a2;
    }

    return e;
}

} // namespace iges
