// iges::GeneralSymbolEntity — Full implementation.

#include "general_symbol_entity.hpp"

namespace iges {

std::expected<GeneralSymbolEntity, Diagnostic>
parse_general_symbol_entity(ParamTokenizer& tok) {
    GeneralSymbolEntity e;

    auto dn = tok.next_pointer(); if (!dn) return std::unexpected(dn.error()); e.denote = *dn;
    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.n = *n;

    e.geometries.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        auto de = tok.next_pointer(); if (!de) return std::unexpected(de.error());
        e.geometries.push_back(*de);
    }

    auto l = tok.next_integer(); if (!l) return std::unexpected(l.error()); e.l = *l;

    e.leaders.reserve(e.l);
    for (int i = 0; i < e.l; ++i) {
        auto de = tok.next_pointer(); if (!de) return std::unexpected(de.error());
        e.leaders.push_back(*de);
    }

    return e;
}

} // namespace iges
