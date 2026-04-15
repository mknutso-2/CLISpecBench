// iges::CylindricalSurfaceEntity — Full implementation.

#include "cylindrical_surface_entity.hpp"

namespace iges {

std::expected<CylindricalSurfaceEntity, Diagnostic>
parse_cylindrical_surface_entity(ParamTokenizer& tok, int form) {
    CylindricalSurfaceEntity e;

    auto deloc = tok.next_pointer(); if (!deloc) return std::unexpected(deloc.error()); e.deloc = *deloc;
    auto deaxis = tok.next_pointer(); if (!deaxis) return std::unexpected(deaxis.error()); e.deaxis = *deaxis;
    auto radius = tok.next_real(); if (!radius) return std::unexpected(radius.error()); e.radius = *radius;

    if (form == 1) {
        auto derefd = tok.next_pointer(); if (!derefd) return std::unexpected(derefd.error()); e.derefd = *derefd;
    }

    return e;
}

} // namespace iges
