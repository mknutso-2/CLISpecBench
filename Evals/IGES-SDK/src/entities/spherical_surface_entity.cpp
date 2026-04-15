// iges::SphericalSurfaceEntity — Full implementation.

#include "spherical_surface_entity.hpp"

namespace iges {

std::expected<SphericalSurfaceEntity, Diagnostic>
parse_spherical_surface_entity(ParamTokenizer& tok, int form) {
    SphericalSurfaceEntity e;

    auto deloc = tok.next_pointer(); if (!deloc) return std::unexpected(deloc.error()); e.deloc = *deloc;
    auto radius = tok.next_real(); if (!radius) return std::unexpected(radius.error()); e.radius = *radius;

    if (form == 1) {
        auto deaxis = tok.next_pointer(); if (!deaxis) return std::unexpected(deaxis.error()); e.deaxis = *deaxis;
        auto derefd = tok.next_pointer(); if (!derefd) return std::unexpected(derefd.error()); e.derefd = *derefd;
    }

    return e;
}

} // namespace iges
