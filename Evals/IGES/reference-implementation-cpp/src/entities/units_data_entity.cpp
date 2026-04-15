// iges::UnitsDataEntity — Full implementation.

#include "units_data_entity.hpp"

namespace iges {

std::expected<UnitsDataEntity, Diagnostic>
parse_units_data_entity(ParamTokenizer& tok) {
    UnitsDataEntity e;

    auto np = tok.next_integer(); if (!np) return std::unexpected(np.error()); e.np = *np;

    e.units.reserve(e.np);
    for (int i = 0; i < e.np; ++i) {
        UnitEntry u;
        auto typ = tok.next_string(); if (!typ) return std::unexpected(typ.error()); u.typ = *typ;
        auto val = tok.next_string(); if (!val) return std::unexpected(val.error()); u.val = *val;
        auto sf  = tok.next_real();   if (!sf)  return std::unexpected(sf.error());  u.sf  = *sf;
        e.units.push_back(std::move(u));
    }

    return e;
}

} // namespace iges
