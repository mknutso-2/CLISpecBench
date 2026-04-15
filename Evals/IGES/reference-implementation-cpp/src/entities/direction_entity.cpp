// iges::DirectionEntity — Type 123 implementation.

#include "direction_entity.hpp"

namespace iges {

std::expected<DirectionEntity, Diagnostic>
parse_direction_entity(ParamTokenizer& tok) {
    DirectionEntity e;

    auto vx = tok.next_real();
    if (!vx) return std::unexpected(vx.error());
    e.x = *vx;

    auto vy = tok.next_real();
    if (!vy) return std::unexpected(vy.error());
    e.y = *vy;

    auto vz = tok.next_real();
    if (!vz) return std::unexpected(vz.error());
    e.z = *vz;

    return e;
}

} // namespace iges
