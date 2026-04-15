// iges::SolidOfLinearExtrusionEntity — Full implementation.

#include "solid_of_linear_extrusion_entity.hpp"

namespace iges {

std::expected<SolidOfLinearExtrusionEntity, Diagnostic>
parse_solid_of_linear_extrusion_entity(ParamTokenizer& tok) {
    SolidOfLinearExtrusionEntity e;

    auto ptr = tok.next_pointer(); if (!ptr) return std::unexpected(ptr.error()); e.ptr = *ptr;
    auto l = tok.next_real(); if (!l) return std::unexpected(l.error()); e.length = *l;

    auto i1 = tok.next_real_or(0.0); if (!i1) return std::unexpected(i1.error()); e.direction.x = *i1;
    auto j1 = tok.next_real_or(0.0); if (!j1) return std::unexpected(j1.error()); e.direction.y = *j1;
    auto k1 = tok.next_real_or(1.0); if (!k1) return std::unexpected(k1.error()); e.direction.z = *k1;

    return e;
}

} // namespace iges
