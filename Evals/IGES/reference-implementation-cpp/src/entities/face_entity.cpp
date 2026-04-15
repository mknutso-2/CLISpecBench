// iges::FaceEntity — Full implementation.

#include "face_entity.hpp"

namespace iges {

std::expected<FaceEntity, Diagnostic>
parse_face_entity(ParamTokenizer& tok) {
    FaceEntity e;

    auto surf = tok.next_pointer(); if (!surf) return std::unexpected(surf.error()); e.surf = *surf;
    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.n = *n;
    auto of = tok.next_logical(); if (!of) return std::unexpected(of.error()); e.outer_loop_flag = *of;

    e.loops.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        auto lp = tok.next_pointer(); if (!lp) return std::unexpected(lp.error());
        e.loops.push_back(*lp);
    }

    return e;
}

} // namespace iges
