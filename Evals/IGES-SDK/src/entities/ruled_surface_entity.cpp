// iges::RuledSurfaceEntity — Full implementation.

#include "ruled_surface_entity.hpp"

namespace iges {

std::expected<RuledSurfaceEntity, Diagnostic>
parse_ruled_surface_entity(ParamTokenizer& tok) {
    RuledSurfaceEntity e;

    auto de1 = tok.next_pointer();
    if (!de1) return std::unexpected(de1.error());
    e.de1 = *de1;

    auto de2 = tok.next_pointer();
    if (!de2) return std::unexpected(de2.error());
    e.de2 = *de2;

    auto dirflg = tok.next_integer();
    if (!dirflg) return std::unexpected(dirflg.error());
    e.dirflg = *dirflg;

    auto devflg = tok.next_integer();
    if (!devflg) return std::unexpected(devflg.error());
    e.devflg = *devflg;

    return e;
}

} // namespace iges
