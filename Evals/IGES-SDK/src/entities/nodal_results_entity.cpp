// iges::NodalResultsEntity — Full implementation.

#include "nodal_results_entity.hpp"

namespace iges {

std::expected<NodalResultsEntity, Diagnostic>
parse_nodal_results_entity(ParamTokenizer& tok) {
    NodalResultsEntity e;

    auto gnote = tok.next_pointer(); if (!gnote) return std::unexpected(gnote.error()); e.gnote = *gnote;
    auto scn   = tok.next_integer(); if (!scn)   return std::unexpected(scn.error());   e.scn = *scn;
    auto time  = tok.next_real();    if (!time)  return std::unexpected(time.error());   e.time = *time;
    auto nv    = tok.next_integer(); if (!nv)    return std::unexpected(nv.error());     e.nv = *nv;
    auto nn    = tok.next_integer(); if (!nn)    return std::unexpected(nn.error());     e.nn = *nn;

    e.nodes.reserve(e.nn);
    for (int i = 0; i < e.nn; ++i) {
        NodalResultsNode node;
        auto node_id = tok.next_integer(); if (!node_id) return std::unexpected(node_id.error());
        node.node_id = *node_id;

        auto np = tok.next_pointer(); if (!np) return std::unexpected(np.error());
        node.np = *np;

        node.values.reserve(e.nv);
        for (int j = 0; j < e.nv; ++j) {
            auto v = tok.next_real(); if (!v) return std::unexpected(v.error());
            node.values.push_back(*v);
        }
        e.nodes.push_back(std::move(node));
    }

    return e;
}

} // namespace iges
