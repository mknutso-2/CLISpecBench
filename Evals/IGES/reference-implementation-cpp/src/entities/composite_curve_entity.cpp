// iges::CompositeCurveEntity — Full implementation.

#include "composite_curve_entity.hpp"

namespace iges {

std::expected<CompositeCurveEntity, Diagnostic>
parse_composite_curve_entity(ParamTokenizer& tok) {
    CompositeCurveEntity e;

    auto n = tok.next_integer();
    if (!n) return std::unexpected(n.error());

    e.constituents.reserve(*n);
    for (int i = 0; i < *n; ++i) {
        auto ptr = tok.next_pointer();
        if (!ptr) return std::unexpected(ptr.error());
        e.constituents.push_back(*ptr);
    }

    return e;
}

} // namespace iges
