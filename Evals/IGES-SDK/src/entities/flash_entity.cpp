// iges::FlashEntity — Full implementation.

#include "flash_entity.hpp"

namespace iges {

std::expected<FlashEntity, Diagnostic>
parse_flash_entity(ParamTokenizer& tok) {
    FlashEntity e;

    auto x = tok.next_real(); if (!x) return std::unexpected(x.error()); e.x = *x;
    auto y = tok.next_real(); if (!y) return std::unexpected(y.error()); e.y = *y;
    auto d1 = tok.next_real(); if (!d1) return std::unexpected(d1.error()); e.dim1 = *d1;
    auto d2 = tok.next_real(); if (!d2) return std::unexpected(d2.error()); e.dim2 = *d2;
    auto rot = tok.next_real(); if (!rot) return std::unexpected(rot.error()); e.rot = *rot;
    auto de = tok.next_pointer(); if (!de) return std::unexpected(de.error()); e.de = *de;

    return e;
}

} // namespace iges
