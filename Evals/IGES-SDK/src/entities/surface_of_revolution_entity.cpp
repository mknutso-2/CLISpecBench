// iges::SurfaceOfRevolutionEntity — Full implementation.

#include "surface_of_revolution_entity.hpp"

namespace iges {

std::expected<SurfaceOfRevolutionEntity, Diagnostic>
parse_surface_of_revolution_entity(ParamTokenizer& tok) {
    SurfaceOfRevolutionEntity e;

    auto l = tok.next_pointer();
    if (!l) return std::unexpected(l.error());
    e.l = *l;

    auto c = tok.next_pointer();
    if (!c) return std::unexpected(c.error());
    e.c = *c;

    auto sa = tok.next_real();
    if (!sa) return std::unexpected(sa.error());
    e.sa = *sa;

    auto ta = tok.next_real();
    if (!ta) return std::unexpected(ta.error());
    e.ta = *ta;

    return e;
}

} // namespace iges
