// iges::SolidOfRevolutionEntity — Full implementation.

#include "solid_of_revolution_entity.hpp"

namespace iges {

std::expected<SolidOfRevolutionEntity, Diagnostic>
parse_solid_of_revolution_entity(ParamTokenizer& tok) {
    SolidOfRevolutionEntity e;

    auto ptr = tok.next_pointer(); if (!ptr) return std::unexpected(ptr.error()); e.ptr = *ptr;
    auto f = tok.next_real_or(1.0); if (!f) return std::unexpected(f.error()); e.f = *f;

    auto x1 = tok.next_real_or(0.0); if (!x1) return std::unexpected(x1.error()); e.axis_point.x = *x1;
    auto y1 = tok.next_real_or(0.0); if (!y1) return std::unexpected(y1.error()); e.axis_point.y = *y1;
    auto z1 = tok.next_real_or(0.0); if (!z1) return std::unexpected(z1.error()); e.axis_point.z = *z1;

    auto i1 = tok.next_real_or(0.0); if (!i1) return std::unexpected(i1.error()); e.axis_dir.x = *i1;
    auto j1 = tok.next_real_or(0.0); if (!j1) return std::unexpected(j1.error()); e.axis_dir.y = *j1;
    auto k1 = tok.next_real_or(1.0); if (!k1) return std::unexpected(k1.error()); e.axis_dir.z = *k1;

    return e;
}

} // namespace iges
