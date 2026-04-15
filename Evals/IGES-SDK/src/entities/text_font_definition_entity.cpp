// iges::TextFontDefinitionEntity — Full implementation.

#include "text_font_definition_entity.hpp"

namespace iges {

std::expected<TextFontDefinitionEntity, Diagnostic>
parse_text_font_definition_entity(ParamTokenizer& tok) {
    TextFontDefinitionEntity e;

    auto fc    = tok.next_integer(); if (!fc)    return std::unexpected(fc.error());    e.fc = *fc;
    auto fname = tok.next_string();  if (!fname) return std::unexpected(fname.error()); e.fname = *fname;
    auto sf    = tok.next_integer(); if (!sf)    return std::unexpected(sf.error());    e.sf = *sf;
    auto scale = tok.next_integer(); if (!scale) return std::unexpected(scale.error()); e.scale = *scale;
    auto n     = tok.next_integer(); if (!n)     return std::unexpected(n.error());     e.n = *n;

    e.characters.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        CharacterDefinition ch;

        auto ac = tok.next_integer(); if (!ac) return std::unexpected(ac.error()); ch.ac = *ac;
        auto nx = tok.next_integer(); if (!nx) return std::unexpected(nx.error()); ch.nx = *nx;
        auto ny = tok.next_integer(); if (!ny) return std::unexpected(ny.error()); ch.ny = *ny;
        auto nm = tok.next_integer(); if (!nm) return std::unexpected(nm.error()); ch.nm = *nm;

        ch.motions.reserve(ch.nm);
        for (int j = 0; j < ch.nm; ++j) {
            PenMotion pm;
            auto pf = tok.next_integer(); if (!pf) return std::unexpected(pf.error()); pm.pf = *pf;
            auto x  = tok.next_integer(); if (!x)  return std::unexpected(x.error());  pm.x = *x;
            auto y  = tok.next_integer(); if (!y)  return std::unexpected(y.error());  pm.y = *y;
            ch.motions.push_back(pm);
        }

        e.characters.push_back(std::move(ch));
    }

    return e;
}

} // namespace iges
