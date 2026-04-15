// iges::TabulatedCylinderEntity — Full implementation.

#include "tabulated_cylinder_entity.hpp"

namespace iges {

std::expected<TabulatedCylinderEntity, Diagnostic>
parse_tabulated_cylinder_entity(ParamTokenizer& tok) {
    TabulatedCylinderEntity e;

    auto de = tok.next_pointer();
    if (!de) return std::unexpected(de.error());
    e.de = *de;

    auto lx = tok.next_real();
    if (!lx) return std::unexpected(lx.error());
    e.terminate_point.x = *lx;

    auto ly = tok.next_real();
    if (!ly) return std::unexpected(ly.error());
    e.terminate_point.y = *ly;

    auto lz = tok.next_real();
    if (!lz) return std::unexpected(lz.error());
    e.terminate_point.z = *lz;

    return e;
}

} // namespace iges
