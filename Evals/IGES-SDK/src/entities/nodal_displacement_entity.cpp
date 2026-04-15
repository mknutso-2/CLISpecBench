// iges::NodalDisplacementEntity — Full implementation.

#include "nodal_displacement_entity.hpp"

namespace iges {

std::expected<NodalDisplacementEntity, Diagnostic>
parse_nodal_displacement_entity(ParamTokenizer& tok) {
    NodalDisplacementEntity e;

    auto nc = tok.next_integer(); if (!nc) return std::unexpected(nc.error()); e.nc = *nc;

    e.gp.reserve(e.nc);
    for (int i = 0; i < e.nc; ++i) {
        auto gp = tok.next_pointer(); if (!gp) return std::unexpected(gp.error());
        e.gp.push_back(*gp);
    }

    auto nn = tok.next_integer(); if (!nn) return std::unexpected(nn.error()); e.nn = *nn;

    e.nodes.reserve(e.nn);
    for (int i = 0; i < e.nn; ++i) {
        NodalDisplacementNode node;

        auto no = tok.next_integer(); if (!no) return std::unexpected(no.error());
        node.node_id = *no;

        auto np = tok.next_pointer(); if (!np) return std::unexpected(np.error());
        node.np = *np;

        node.cases.reserve(e.nc);
        for (int c = 0; c < e.nc; ++c) {
            NodalDisplacementValues v;
            auto x  = tok.next_real(); if (!x)  return std::unexpected(x.error());  v.x  = *x;
            auto y  = tok.next_real(); if (!y)  return std::unexpected(y.error());  v.y  = *y;
            auto z  = tok.next_real(); if (!z)  return std::unexpected(z.error());  v.z  = *z;
            auto rx = tok.next_real(); if (!rx) return std::unexpected(rx.error()); v.rx = *rx;
            auto ry = tok.next_real(); if (!ry) return std::unexpected(ry.error()); v.ry = *ry;
            auto rz = tok.next_real(); if (!rz) return std::unexpected(rz.error()); v.rz = *rz;
            node.cases.push_back(v);
        }
        e.nodes.push_back(std::move(node));
    }

    return e;
}

} // namespace iges
