// iges::PlaneSurfaceEntity — Full implementation.

#include "plane_surface_entity.hpp"

namespace iges {

std::expected<PlaneSurfaceEntity, Diagnostic>
parse_plane_surface_entity(ParamTokenizer& tok, int form) {
    PlaneSurfaceEntity e;

    auto deloc = tok.next_pointer(); if (!deloc) return std::unexpected(deloc.error()); e.deloc = *deloc;
    auto denrml = tok.next_pointer(); if (!denrml) return std::unexpected(denrml.error()); e.denrml = *denrml;

    if (form == 1) {
        auto derefd = tok.next_pointer(); if (!derefd) return std::unexpected(derefd.error()); e.derefd = *derefd;
    }

    return e;
}

} // namespace iges
