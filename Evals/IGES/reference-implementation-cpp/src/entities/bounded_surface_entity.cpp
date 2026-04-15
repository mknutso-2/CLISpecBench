// iges::BoundedSurfaceEntity — Full implementation.

#include "bounded_surface_entity.hpp"

namespace iges {

std::expected<BoundedSurfaceEntity, Diagnostic>
parse_bounded_surface_entity(ParamTokenizer& tok) {
    BoundedSurfaceEntity e;

    auto type = tok.next_integer();
    if (!type) return std::unexpected(type.error());
    e.type = *type;

    auto sptr = tok.next_pointer();
    if (!sptr) return std::unexpected(sptr.error());
    e.sptr = *sptr;

    auto n = tok.next_integer();
    if (!n) return std::unexpected(n.error());
    e.n = *n;

    e.bdpt.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        auto ptr = tok.next_pointer();
        if (!ptr) return std::unexpected(ptr.error());
        e.bdpt.push_back(*ptr);
    }

    return e;
}

} // namespace iges
