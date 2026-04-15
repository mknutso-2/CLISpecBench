// iges::TrimmedSurfaceEntity — Full implementation.

#include "trimmed_surface_entity.hpp"

namespace iges {

std::expected<TrimmedSurfaceEntity, Diagnostic>
parse_trimmed_surface_entity(ParamTokenizer& tok) {
    TrimmedSurfaceEntity e;

    auto pts = tok.next_pointer();
    if (!pts) return std::unexpected(pts.error());
    e.pts = *pts;

    auto n1 = tok.next_integer();
    if (!n1) return std::unexpected(n1.error());
    e.n1 = *n1;

    auto n2 = tok.next_integer();
    if (!n2) return std::unexpected(n2.error());
    e.n2 = *n2;

    auto pto = tok.next_pointer();
    if (!pto) return std::unexpected(pto.error());
    e.pto = *pto;

    e.pti.reserve(e.n2);
    for (int i = 0; i < e.n2; ++i) {
        auto ptr = tok.next_pointer();
        if (!ptr) return std::unexpected(ptr.error());
        e.pti.push_back(*ptr);
    }

    return e;
}

} // namespace iges
