// iges::GeneralNoteEntity — Full implementation.

#include "general_note_entity.hpp"

namespace iges {

std::expected<GeneralNoteEntity, Diagnostic>
parse_general_note_entity(ParamTokenizer& tok) {
    GeneralNoteEntity e;

    auto ns = tok.next_integer(); if (!ns) return std::unexpected(ns.error()); e.ns = *ns;

    e.strings.reserve(e.ns);
    for (int i = 0; i < e.ns; ++i) {
        NoteString s;
        auto nc = tok.next_integer(); if (!nc) return std::unexpected(nc.error()); s.nc = *nc;
        auto wc = tok.next_real(); if (!wc) return std::unexpected(wc.error()); s.wc = *wc;
        auto hc = tok.next_real(); if (!hc) return std::unexpected(hc.error()); s.hc = *hc;
        auto fc = tok.next_integer(); if (!fc) return std::unexpected(fc.error()); s.fc = *fc;
        auto sl = tok.next_real(); if (!sl) return std::unexpected(sl.error()); s.slant = *sl;
        auto a = tok.next_real(); if (!a) return std::unexpected(a.error()); s.angle = *a;
        auto m = tok.next_integer(); if (!m) return std::unexpected(m.error()); s.mirror = *m;
        auto vh = tok.next_integer(); if (!vh) return std::unexpected(vh.error()); s.vh = *vh;
        auto x = tok.next_real(); if (!x) return std::unexpected(x.error()); s.start.x = *x;
        auto y = tok.next_real(); if (!y) return std::unexpected(y.error()); s.start.y = *y;
        auto z = tok.next_real(); if (!z) return std::unexpected(z.error()); s.start.z = *z;
        auto t = tok.next_string(); if (!t) return std::unexpected(t.error()); s.text = *t;
        e.strings.push_back(std::move(s));
    }

    return e;
}

} // namespace iges
