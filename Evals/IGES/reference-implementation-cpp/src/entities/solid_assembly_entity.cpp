// iges::SolidAssemblyEntity — Full implementation.

#include "solid_assembly_entity.hpp"

namespace iges {

std::expected<SolidAssemblyEntity, Diagnostic>
parse_solid_assembly_entity(ParamTokenizer& tok) {
    SolidAssemblyEntity e;

    auto n = tok.next_integer();
    if (!n) return std::unexpected(n.error());
    e.n = *n;

    e.items.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        auto p = tok.next_pointer();
        if (!p) return std::unexpected(p.error());
        e.items.push_back(*p);
    }

    e.transforms.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        auto p = tok.next_pointer();
        if (!p) return std::unexpected(p.error());
        e.transforms.push_back(*p);
    }

    return e;
}

} // namespace iges
