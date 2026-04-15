// iges::OffsetCurveEntity — Full implementation.

#include "offset_curve_entity.hpp"

namespace iges {

std::expected<OffsetCurveEntity, Diagnostic>
parse_offset_curve_entity(ParamTokenizer& tok) {
    OffsetCurveEntity e;

    auto de1 = tok.next_pointer();
    if (!de1) return std::unexpected(de1.error());
    e.de1 = *de1;

    auto flag = tok.next_integer();
    if (!flag) return std::unexpected(flag.error());
    e.flag = *flag;

    auto de2 = tok.next_pointer();
    if (!de2) return std::unexpected(de2.error());
    e.de2 = *de2;

    auto ndim = tok.next_integer();
    if (!ndim) return std::unexpected(ndim.error());
    e.ndim = *ndim;

    auto ptype = tok.next_integer();
    if (!ptype) return std::unexpected(ptype.error());
    e.ptype = *ptype;

    auto d1 = tok.next_real();
    if (!d1) return std::unexpected(d1.error());
    e.d1 = *d1;

    auto td1 = tok.next_real();
    if (!td1) return std::unexpected(td1.error());
    e.td1 = *td1;

    auto d2 = tok.next_real();
    if (!d2) return std::unexpected(d2.error());
    e.d2 = *d2;

    auto td2 = tok.next_real();
    if (!td2) return std::unexpected(td2.error());
    e.td2 = *td2;

    auto vx = tok.next_real();
    if (!vx) return std::unexpected(vx.error());
    e.vx = *vx;

    auto vy = tok.next_real();
    if (!vy) return std::unexpected(vy.error());
    e.vy = *vy;

    auto vz = tok.next_real();
    if (!vz) return std::unexpected(vz.error());
    e.vz = *vz;

    auto tt1 = tok.next_real();
    if (!tt1) return std::unexpected(tt1.error());
    e.tt1 = *tt1;

    auto tt2 = tok.next_real();
    if (!tt2) return std::unexpected(tt2.error());
    e.tt2 = *tt2;

    return e;
}

} // namespace iges
