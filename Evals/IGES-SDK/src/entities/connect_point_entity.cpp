// iges::ConnectPointEntity — Full implementation.

#include "connect_point_entity.hpp"

namespace iges {

std::expected<ConnectPointEntity, Diagnostic>
parse_connect_point_entity(ParamTokenizer& tok) {
    ConnectPointEntity e;

    auto x = tok.next_real(); if (!x) return std::unexpected(x.error()); e.location.x = *x;
    auto y = tok.next_real(); if (!y) return std::unexpected(y.error()); e.location.y = *y;
    auto z = tok.next_real(); if (!z) return std::unexpected(z.error()); e.location.z = *z;
    auto ptr = tok.next_pointer(); if (!ptr) return std::unexpected(ptr.error()); e.display_symbol = *ptr;
    auto tf = tok.next_integer(); if (!tf) return std::unexpected(tf.error()); e.tf = *tf;
    auto ff = tok.next_integer(); if (!ff) return std::unexpected(ff.error()); e.ff = *ff;
    auto cid = tok.next_string(); if (!cid) return std::unexpected(cid.error()); e.cid = *cid;
    auto pttcid = tok.next_pointer(); if (!pttcid) return std::unexpected(pttcid.error()); e.pttcid = *pttcid;
    auto cfn = tok.next_string(); if (!cfn) return std::unexpected(cfn.error()); e.cfn = *cfn;
    auto pttcfn = tok.next_pointer(); if (!pttcfn) return std::unexpected(pttcfn.error()); e.pttcfn = *pttcfn;
    auto cpid = tok.next_integer(); if (!cpid) return std::unexpected(cpid.error()); e.cpid = *cpid;
    auto fc = tok.next_integer(); if (!fc) return std::unexpected(fc.error()); e.fc = *fc;
    auto sf = tok.next_integer(); if (!sf) return std::unexpected(sf.error()); e.sf = *sf;
    auto psfi = tok.next_pointer(); if (!psfi) return std::unexpected(psfi.error()); e.psfi = *psfi;

    return e;
}

} // namespace iges
