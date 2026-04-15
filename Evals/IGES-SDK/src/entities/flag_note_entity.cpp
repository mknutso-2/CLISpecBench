// iges::FlagNoteEntity — Full implementation.

#include "flag_note_entity.hpp"

namespace iges {

std::expected<FlagNoteEntity, Diagnostic>
parse_flag_note_entity(ParamTokenizer& tok) {
    FlagNoteEntity e;

    auto xt = tok.next_real(); if (!xt) return std::unexpected(xt.error()); e.xt = *xt;
    auto yt = tok.next_real(); if (!yt) return std::unexpected(yt.error()); e.yt = *yt;
    auto zt = tok.next_real(); if (!zt) return std::unexpected(zt.error()); e.zt = *zt;
    auto a = tok.next_real(); if (!a) return std::unexpected(a.error()); e.angle = *a;
    auto dn = tok.next_pointer(); if (!dn) return std::unexpected(dn.error()); e.denote = *dn;
    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.n = *n;

    e.leaders.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        auto de = tok.next_pointer(); if (!de) return std::unexpected(de.error());
        e.leaders.push_back(*de);
    }

    return e;
}

} // namespace iges
