// iges::PlaneEntity — Type 108 implementation.

#include "plane_entity.hpp"

namespace iges {

std::expected<PlaneEntity, Diagnostic>
parse_plane_entity(ParamTokenizer& tok) {
    PlaneEntity e;

    auto va = tok.next_real();
    if (!va) return std::unexpected(va.error());
    e.A = *va;

    auto vb = tok.next_real();
    if (!vb) return std::unexpected(vb.error());
    e.B = *vb;

    auto vc = tok.next_real();
    if (!vc) return std::unexpected(vc.error());
    e.C = *vc;

    auto vd = tok.next_real();
    if (!vd) return std::unexpected(vd.error());
    e.D = *vd;

    auto vptr = tok.next_pointer();
    if (!vptr) return std::unexpected(vptr.error());
    e.ptr = DEIndex{*vptr};

    auto vx = tok.next_real();
    if (!vx) return std::unexpected(vx.error());
    e.x = *vx;

    auto vy = tok.next_real();
    if (!vy) return std::unexpected(vy.error());
    e.y = *vy;

    auto vz = tok.next_real();
    if (!vz) return std::unexpected(vz.error());
    e.z = *vz;

    auto vsz = tok.next_real();
    if (!vsz) return std::unexpected(vsz.error());
    e.size = *vsz;

    return e;
}

} // namespace iges
