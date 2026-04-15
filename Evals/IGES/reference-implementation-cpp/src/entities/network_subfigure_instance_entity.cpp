// iges::NetworkSubfigureInstanceEntity — Full implementation.

#include "network_subfigure_instance_entity.hpp"

namespace iges {

std::expected<NetworkSubfigureInstanceEntity, Diagnostic>
parse_network_subfigure_instance_entity(ParamTokenizer& tok) {
    NetworkSubfigureInstanceEntity e;

    auto de = tok.next_pointer(); if (!de) return std::unexpected(de.error()); e.de = *de;
    auto x  = tok.next_real();    if (!x)  return std::unexpected(x.error());  e.x  = *x;
    auto y  = tok.next_real();    if (!y)  return std::unexpected(y.error());  e.y  = *y;
    auto z  = tok.next_real();    if (!z)  return std::unexpected(z.error());  e.z  = *z;
    auto xs = tok.next_real();    if (!xs) return std::unexpected(xs.error()); e.xs = *xs;
    auto ys = tok.next_real();    if (!ys) return std::unexpected(ys.error()); e.ys = *ys;
    auto zs = tok.next_real();    if (!zs) return std::unexpected(zs.error()); e.zs = *zs;
    auto tf = tok.next_integer(); if (!tf) return std::unexpected(tf.error()); e.tf = *tf;

    auto prd  = tok.next_string();  if (!prd)  return std::unexpected(prd.error());  e.prd  = *prd;
    auto dptr = tok.next_pointer(); if (!dptr) return std::unexpected(dptr.error()); e.dptr = *dptr;
    auto nc   = tok.next_integer(); if (!nc)   return std::unexpected(nc.error());   e.nc   = *nc;

    e.cptrs.reserve(e.nc);
    for (int i = 0; i < e.nc; ++i) {
        auto p = tok.next_pointer(); if (!p) return std::unexpected(p.error());
        e.cptrs.push_back(*p);
    }

    return e;
}

} // namespace iges
