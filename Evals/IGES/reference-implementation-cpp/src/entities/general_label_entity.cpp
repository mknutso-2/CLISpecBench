// iges::GeneralLabelEntity — Full implementation.

#include "general_label_entity.hpp"

namespace iges {

std::expected<GeneralLabelEntity, Diagnostic>
parse_general_label_entity(ParamTokenizer& tok) {
    GeneralLabelEntity e;

    auto n_note = tok.next_pointer(); if (!n_note) return std::unexpected(n_note.error()); e.denote = *n_note;
    auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); e.n = *n;

    e.leaders.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        auto de = tok.next_pointer(); if (!de) return std::unexpected(de.error());
        e.leaders.push_back(*de);
    }

    return e;
}

} // namespace iges
