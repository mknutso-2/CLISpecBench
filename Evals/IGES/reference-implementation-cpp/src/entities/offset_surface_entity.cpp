// iges::OffsetSurfaceEntity — Full implementation.

#include "offset_surface_entity.hpp"

namespace iges {

std::expected<OffsetSurfaceEntity, Diagnostic>
parse_offset_surface_entity(ParamTokenizer& tok) {
    OffsetSurfaceEntity e;

    auto nx = tok.next_real();
    if (!nx) return std::unexpected(nx.error());
    e.nx = *nx;

    auto ny = tok.next_real();
    if (!ny) return std::unexpected(ny.error());
    e.ny = *ny;

    auto nz = tok.next_real();
    if (!nz) return std::unexpected(nz.error());
    e.nz = *nz;

    auto d = tok.next_real();
    if (!d) return std::unexpected(d.error());
    e.d = *d;

    auto de = tok.next_pointer();
    if (!de) return std::unexpected(de.error());
    e.de = *de;

    return e;
}

} // namespace iges
