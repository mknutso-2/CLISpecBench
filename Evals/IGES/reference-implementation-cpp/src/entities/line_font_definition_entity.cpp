// iges::LineFontDefinitionEntity — Full implementation.

#include "line_font_definition_entity.hpp"

namespace iges {

std::expected<LineFontDefinitionEntity, Diagnostic>
parse_line_font_definition_entity(ParamTokenizer& tok, int form) {
    LineFontDefinitionEntity e;
    e.form = form;

    auto m = tok.next_integer(); if (!m) return std::unexpected(m.error()); e.m = *m;

    if (form == 1) {
        // Form 1: M is display flag, followed by L1 (pointer), L2 (real), L3 (real)
        auto l1 = tok.next_pointer(); if (!l1) return std::unexpected(l1.error()); e.l1 = *l1;
        auto l2 = tok.next_real(); if (!l2) return std::unexpected(l2.error()); e.l2 = *l2;
        auto l3 = tok.next_real(); if (!l3) return std::unexpected(l3.error()); e.l3 = *l3;
    } else {
        // Form 2: M segment lengths followed by hex bitmask string B
        e.segments.reserve(e.m);
        for (int i = 0; i < e.m; ++i) {
            auto s = tok.next_real(); if (!s) return std::unexpected(s.error());
            e.segments.push_back(*s);
        }
        auto b = tok.next_string(); if (!b) return std::unexpected(b.error()); e.bitmask = *b;
    }

    return e;
}

} // namespace iges
