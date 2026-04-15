// iges::ToroidalSurfaceEntity — Full implementation.

#include "toroidal_surface_entity.hpp"

namespace iges {

std::expected<ToroidalSurfaceEntity, Diagnostic>
parse_toroidal_surface_entity(ParamTokenizer& tok, int form) {
    ToroidalSurfaceEntity e;

    auto deloc = tok.next_pointer(); if (!deloc) return std::unexpected(deloc.error()); e.deloc = *deloc;
    auto deaxis = tok.next_pointer(); if (!deaxis) return std::unexpected(deaxis.error()); e.deaxis = *deaxis;
    auto majrad = tok.next_real(); if (!majrad) return std::unexpected(majrad.error()); e.majrad = *majrad;
    auto minrad = tok.next_real(); if (!minrad) return std::unexpected(minrad.error()); e.minrad = *minrad;

    if (form == 1) {
        auto derefd = tok.next_pointer(); if (!derefd) return std::unexpected(derefd.error()); e.derefd = *derefd;
    }

    return e;
}

} // namespace iges
