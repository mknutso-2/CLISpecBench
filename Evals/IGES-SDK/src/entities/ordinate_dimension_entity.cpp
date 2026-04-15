// iges::OrdinateDimensionEntity — Full implementation.

#include "ordinate_dimension_entity.hpp"

namespace iges {

std::expected<OrdinateDimensionEntity, Diagnostic>
parse_ordinate_dimension_entity(ParamTokenizer& tok, int form) {
    OrdinateDimensionEntity e;
    e.form = form;

    auto n = tok.next_pointer(); if (!n) return std::unexpected(n.error()); e.denote = *n;

    if (form == 1) {
        auto o = tok.next_pointer(); if (!o) return std::unexpected(o.error()); e.deord = *o;
        auto s = tok.next_pointer(); if (!s) return std::unexpected(s.error()); e.desupp = *s;
    } else {
        auto w = tok.next_pointer(); if (!w) return std::unexpected(w.error()); e.dewit = *w;
    }

    return e;
}

} // namespace iges
