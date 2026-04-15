// iges::VertexListEntity — Full implementation.

#include "vertex_list_entity.hpp"

namespace iges {

std::expected<VertexListEntity, Diagnostic>
parse_vertex_list_entity(ParamTokenizer& tok) {
    VertexListEntity e;

    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.n = *n;

    e.vertices.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        Vec3 v;
        auto x = tok.next_real(); if (!x) return std::unexpected(x.error()); v.x = *x;
        auto y = tok.next_real(); if (!y) return std::unexpected(y.error()); v.y = *y;
        auto z = tok.next_real(); if (!z) return std::unexpected(z.error()); v.z = *z;
        e.vertices.push_back(v);
    }

    return e;
}

} // namespace iges
