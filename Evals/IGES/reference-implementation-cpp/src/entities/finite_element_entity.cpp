// iges::FiniteElementEntity — Full implementation.

#include "finite_element_entity.hpp"

namespace iges {

std::expected<FiniteElementEntity, Diagnostic>
parse_finite_element_entity(ParamTokenizer& tok) {
    FiniteElementEntity e;

    auto itop = tok.next_integer(); if (!itop) return std::unexpected(itop.error()); e.itop = *itop;
    auto n = tok.next_integer();    if (!n) return std::unexpected(n.error());       e.n = *n;

    e.nodes.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        auto de = tok.next_pointer(); if (!de) return std::unexpected(de.error());
        e.nodes.push_back(*de);
    }

    auto etyp = tok.next_string(); if (!etyp) return std::unexpected(etyp.error());
    e.etyp = *etyp;

    return e;
}

} // namespace iges
