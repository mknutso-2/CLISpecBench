// iges::NetworkSubfigureDefinitionEntity — Full implementation.

#include "network_subfigure_definition_entity.hpp"

namespace iges {

std::expected<NetworkSubfigureDefinitionEntity, Diagnostic>
parse_network_subfigure_definition_entity(ParamTokenizer& tok) {
    NetworkSubfigureDefinitionEntity e;

    auto depth = tok.next_integer(); if (!depth) return std::unexpected(depth.error()); e.depth = *depth;
    auto name  = tok.next_string();  if (!name)  return std::unexpected(name.error());  e.name  = *name;
    auto na    = tok.next_integer(); if (!na)    return std::unexpected(na.error());    e.na    = *na;

    e.associated.reserve(e.na);
    for (int i = 0; i < e.na; ++i) {
        auto p = tok.next_pointer(); if (!p) return std::unexpected(p.error());
        e.associated.push_back(*p);
    }

    auto tf   = tok.next_integer(); if (!tf)   return std::unexpected(tf.error());   e.tf   = *tf;
    auto prd  = tok.next_string();  if (!prd)  return std::unexpected(prd.error());  e.prd  = *prd;
    auto dptr = tok.next_pointer(); if (!dptr) return std::unexpected(dptr.error()); e.dptr = *dptr;
    auto nc   = tok.next_integer(); if (!nc)   return std::unexpected(nc.error());   e.nc   = *nc;

    e.connects.reserve(e.nc);
    for (int i = 0; i < e.nc; ++i) {
        auto p = tok.next_pointer(); if (!p) return std::unexpected(p.error());
        e.connects.push_back(*p);
    }

    return e;
}

} // namespace iges
