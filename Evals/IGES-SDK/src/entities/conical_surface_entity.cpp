// iges::ConicalSurfaceEntity — Full implementation.

#include "conical_surface_entity.hpp"

namespace iges {

std::expected<ConicalSurfaceEntity, Diagnostic>
parse_conical_surface_entity(ParamTokenizer& tok, int form) {
    ConicalSurfaceEntity e;

    auto deloc = tok.next_pointer(); if (!deloc) return std::unexpected(deloc.error()); e.deloc = *deloc;
    auto deaxis = tok.next_pointer(); if (!deaxis) return std::unexpected(deaxis.error()); e.deaxis = *deaxis;
    auto radius = tok.next_real(); if (!radius) return std::unexpected(radius.error()); e.radius = *radius;
    auto sangle = tok.next_real(); if (!sangle) return std::unexpected(sangle.error()); e.sangle = *sangle;

    if (form == 1) {
        auto derefd = tok.next_pointer(); if (!derefd) return std::unexpected(derefd.error()); e.derefd = *derefd;
    }

    return e;
}

} // namespace iges
