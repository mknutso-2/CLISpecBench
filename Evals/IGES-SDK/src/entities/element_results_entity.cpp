// iges::ElementResultsEntity — Full implementation.

#include "element_results_entity.hpp"

namespace iges {

std::expected<ElementResultsEntity, Diagnostic>
parse_element_results_entity(ParamTokenizer& tok) {
    ElementResultsEntity e;

    auto gnote = tok.next_pointer(); if (!gnote) return std::unexpected(gnote.error()); e.gnote = *gnote;
    auto scn   = tok.next_integer(); if (!scn)   return std::unexpected(scn.error());   e.scn = *scn;
    auto time  = tok.next_real();    if (!time)  return std::unexpected(time.error());   e.time = *time;
    auto nv    = tok.next_integer(); if (!nv)    return std::unexpected(nv.error());     e.nv = *nv;
    auto rrf   = tok.next_integer(); if (!rrf)   return std::unexpected(rrf.error());     e.rrf = *rrf;
    auto ne    = tok.next_integer(); if (!ne)    return std::unexpected(ne.error());     e.ne = *ne;

    e.elements.reserve(e.ne);
    for (int i = 0; i < e.ne; ++i) {
        ElementResultsElement elem;

        auto en   = tok.next_integer(); if (!en)   return std::unexpected(en.error());   elem.en = *en;
        auto ep   = tok.next_pointer(); if (!ep)   return std::unexpected(ep.error());   elem.ep = *ep;
        auto itop = tok.next_integer(); if (!itop) return std::unexpected(itop.error()); elem.itop = *itop;
        auto nl   = tok.next_integer(); if (!nl)   return std::unexpected(nl.error());   elem.nl = *nl;
        auto dlf  = tok.next_integer(); if (!dlf)  return std::unexpected(dlf.error());  elem.dlf = *dlf;
        auto nrl  = tok.next_integer(); if (!nrl)  return std::unexpected(nrl.error());  elem.nrl = *nrl;

        elem.rdrl.reserve(elem.nrl);
        for (int j = 0; j < elem.nrl; ++j) {
            auto r = tok.next_integer(); if (!r) return std::unexpected(r.error());
            elem.rdrl.push_back(*r);
        }

        auto numv = tok.next_integer(); if (!numv) return std::unexpected(numv.error()); elem.numv = *numv;

        elem.values.reserve(elem.numv);
        for (int j = 0; j < elem.numv; ++j) {
            auto v = tok.next_real(); if (!v) return std::unexpected(v.error());
            elem.values.push_back(*v);
        }

        e.elements.push_back(std::move(elem));
    }

    return e;
}

} // namespace iges
