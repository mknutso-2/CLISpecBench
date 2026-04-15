// iges::CurveOnParametricSurfaceEntity — Full implementation.

#include "curve_on_surface_entity.hpp"

namespace iges {

std::expected<CurveOnParametricSurfaceEntity, Diagnostic>
parse_curve_on_surface_entity(ParamTokenizer& tok) {
    CurveOnParametricSurfaceEntity e;

    auto crtn = tok.next_integer();
    if (!crtn) return std::unexpected(crtn.error());
    e.crtn = *crtn;

    auto sptr = tok.next_pointer();
    if (!sptr) return std::unexpected(sptr.error());
    e.sptr = *sptr;

    auto bptr = tok.next_pointer();
    if (!bptr) return std::unexpected(bptr.error());
    e.bptr = *bptr;

    auto cptr = tok.next_pointer();
    if (!cptr) return std::unexpected(cptr.error());
    e.cptr = *cptr;

    auto pref = tok.next_integer();
    if (!pref) return std::unexpected(pref.error());
    e.pref = *pref;

    return e;
}

} // namespace iges
