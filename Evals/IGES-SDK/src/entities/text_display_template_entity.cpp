// iges::TextDisplayTemplateEntity — Full implementation.

#include "text_display_template_entity.hpp"

namespace iges {

std::expected<TextDisplayTemplateEntity, Diagnostic>
parse_text_display_template_entity(ParamTokenizer& tok) {
    TextDisplayTemplateEntity e;

    auto cbw = tok.next_real(); if (!cbw) return std::unexpected(cbw.error()); e.cbw = *cbw;
    auto cbh = tok.next_real(); if (!cbh) return std::unexpected(cbh.error()); e.cbh = *cbh;
    auto fc  = tok.next_integer(); if (!fc) return std::unexpected(fc.error()); e.fc = *fc;
    auto sl  = tok.next_real(); if (!sl) return std::unexpected(sl.error()); e.sl = *sl;
    auto a   = tok.next_real(); if (!a) return std::unexpected(a.error()); e.a = *a;
    auto m   = tok.next_integer(); if (!m) return std::unexpected(m.error()); e.m = *m;
    auto vh  = tok.next_integer(); if (!vh) return std::unexpected(vh.error()); e.vh = *vh;
    auto xs  = tok.next_real(); if (!xs) return std::unexpected(xs.error()); e.xs = *xs;
    auto ys  = tok.next_real(); if (!ys) return std::unexpected(ys.error()); e.ys = *ys;
    auto zs  = tok.next_real(); if (!zs) return std::unexpected(zs.error()); e.zs = *zs;

    return e;
}

} // namespace iges
