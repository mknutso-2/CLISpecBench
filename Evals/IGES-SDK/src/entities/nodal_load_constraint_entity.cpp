// iges::NodalLoadConstraintEntity — Full implementation.

#include "nodal_load_constraint_entity.hpp"

namespace iges {

std::expected<NodalLoadConstraintEntity, Diagnostic>
parse_nodal_load_constraint_entity(ParamTokenizer& tok) {
    NodalLoadConstraintEntity e;

    auto nc   = tok.next_integer(); if (!nc)   return std::unexpected(nc.error());   e.nc   = *nc;
    auto type = tok.next_integer(); if (!type) return std::unexpected(type.error()); e.type = *type;
    auto de   = tok.next_pointer(); if (!de)   return std::unexpected(de.error());   e.de   = *de;

    e.ptrs.reserve(e.nc);
    for (int i = 0; i < e.nc; ++i) {
        auto p = tok.next_pointer(); if (!p) return std::unexpected(p.error());
        e.ptrs.push_back(*p);
    }

    return e;
}

} // namespace iges
