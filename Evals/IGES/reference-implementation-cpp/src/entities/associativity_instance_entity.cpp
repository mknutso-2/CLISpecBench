// iges::AssociativityInstanceEntity — Full implementation.

#include "associativity_instance_entity.hpp"

namespace iges {

std::expected<AssociativityInstanceEntity, Diagnostic>
parse_associativity_instance_entity(ParamTokenizer& tok) {
    AssociativityInstanceEntity e;

    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.n = *n;

    e.entries.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        auto de = tok.next_pointer(); if (!de) return std::unexpected(de.error());
        e.entries.push_back(*de);
    }

    return e;
}

} // namespace iges
