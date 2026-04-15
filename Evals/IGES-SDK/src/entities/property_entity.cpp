// iges::PropertyEntity — Full implementation.

#include "property_entity.hpp"

namespace iges {

std::expected<PropertyEntity, Diagnostic>
parse_property_entity(ParamTokenizer& tok) {
    PropertyEntity e;

    auto np = tok.next_integer(); if (!np) return std::unexpected(np.error()); e.np = *np;

    e.values.reserve(e.np);
    for (int i = 0; i < e.np; ++i) {
        auto v = tok.next_field(); if (!v) return std::unexpected(v.error());
        e.values.push_back(*v);
    }

    return e;
}

} // namespace iges
