// iges::BoundaryEntity — Full implementation.

#include "boundary_entity.hpp"

namespace iges {

std::expected<BoundaryEntity, Diagnostic>
parse_boundary_entity(ParamTokenizer& tok) {
    BoundaryEntity e;

    auto type = tok.next_integer();
    if (!type) return std::unexpected(type.error());
    e.type = *type;

    auto pref = tok.next_integer();
    if (!pref) return std::unexpected(pref.error());
    e.pref = *pref;

    auto sptr = tok.next_pointer();
    if (!sptr) return std::unexpected(sptr.error());
    e.sptr = *sptr;

    auto n = tok.next_integer();
    if (!n) return std::unexpected(n.error());
    e.n = *n;

    e.curves.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        BoundaryCurve bc;

        auto crvpt = tok.next_pointer();
        if (!crvpt) return std::unexpected(crvpt.error());
        bc.crvpt = *crvpt;

        auto sense = tok.next_integer();
        if (!sense) return std::unexpected(sense.error());
        bc.sense = *sense;

        auto k = tok.next_integer();
        if (!k) return std::unexpected(k.error());
        bc.k = *k;

        bc.pscpt.reserve(bc.k);
        for (int j = 0; j < bc.k; ++j) {
            auto p = tok.next_pointer();
            if (!p) return std::unexpected(p.error());
            bc.pscpt.push_back(*p);
        }

        e.curves.push_back(std::move(bc));
    }

    return e;
}

} // namespace iges
