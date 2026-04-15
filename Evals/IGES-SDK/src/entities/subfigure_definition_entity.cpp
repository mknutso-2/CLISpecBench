// iges::SubfigureDefinitionEntity — Full implementation.

#include "subfigure_definition_entity.hpp"

namespace iges {

std::expected<SubfigureDefinitionEntity, Diagnostic>
parse_subfigure_definition_entity(ParamTokenizer& tok) {
    SubfigureDefinitionEntity e;

    auto depth = tok.next_integer(); if (!depth) return std::unexpected(depth.error()); e.depth = *depth;
    auto name = tok.next_string(); if (!name) return std::unexpected(name.error()); e.name = *name;
    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.n = *n;

    e.entities.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        auto de = tok.next_pointer(); if (!de) return std::unexpected(de.error());
        e.entities.push_back(*de);
    }

    return e;
}

} // namespace iges
