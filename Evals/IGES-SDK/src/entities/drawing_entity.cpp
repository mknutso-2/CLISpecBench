// iges::DrawingEntity — Full implementation.

#include "drawing_entity.hpp"

namespace iges {

std::expected<DrawingEntity, Diagnostic>
parse_drawing_entity(ParamTokenizer& tok, int form) {
    DrawingEntity e;

    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.n = *n;

    e.views.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        DrawingView dv;
        auto v = tok.next_pointer(); if (!v) return std::unexpected(v.error()); dv.view = *v;
        auto x = tok.next_real(); if (!x) return std::unexpected(x.error()); dv.x_origin = *x;
        auto y = tok.next_real(); if (!y) return std::unexpected(y.error()); dv.y_origin = *y;
        if (form == 1) {
            auto a = tok.next_real(); if (!a) return std::unexpected(a.error()); dv.angle = *a;
        }
        e.views.push_back(dv);
    }

    auto m = tok.next_integer_or(0); if (!m) return std::unexpected(m.error()); e.m = *m;

    e.annotations.reserve(e.m);
    for (int i = 0; i < e.m; ++i) {
        auto a = tok.next_pointer(); if (!a) return std::unexpected(a.error());
        e.annotations.push_back(*a);
    }

    return e;
}

} // namespace iges
