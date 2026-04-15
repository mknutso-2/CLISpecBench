// iges::SubfigureInstanceEntity — Full implementation.

#include "subfigure_instance_entity.hpp"

namespace iges {

std::expected<SubfigureInstanceEntity, Diagnostic>
parse_subfigure_instance_entity(ParamTokenizer& tok) {
    SubfigureInstanceEntity e;

    auto de = tok.next_pointer(); if (!de) return std::unexpected(de.error()); e.de = *de;
    auto x = tok.next_real(); if (!x) return std::unexpected(x.error()); e.translation.x = *x;
    auto y = tok.next_real(); if (!y) return std::unexpected(y.error()); e.translation.y = *y;
    auto z = tok.next_real(); if (!z) return std::unexpected(z.error()); e.translation.z = *z;
    auto s = tok.next_real_or(1.0); if (!s) return std::unexpected(s.error()); e.scale = *s;

    return e;
}

} // namespace iges
