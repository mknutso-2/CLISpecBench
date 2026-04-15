// iges::ColorDefinitionEntity — Full implementation.

#include "color_definition_entity.hpp"

namespace iges {

std::expected<ColorDefinitionEntity, Diagnostic>
parse_color_definition_entity(ParamTokenizer& tok) {
    ColorDefinitionEntity e;

    auto r = tok.next_real(); if (!r) return std::unexpected(r.error()); e.red = *r;
    auto g = tok.next_real(); if (!g) return std::unexpected(g.error()); e.green = *g;
    auto b = tok.next_real(); if (!b) return std::unexpected(b.error()); e.blue = *b;
    auto name = tok.next_string_or(""); if (!name) return std::unexpected(name.error()); e.name = *name;

    return e;
}

} // namespace iges
