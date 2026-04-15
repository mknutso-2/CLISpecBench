// iges::BooleanTreeEntity — Full implementation.

#include "boolean_tree_entity.hpp"

namespace iges {

std::expected<BooleanTreeEntity, Diagnostic>
parse_boolean_tree_entity(ParamTokenizer& tok) {
    BooleanTreeEntity e;

    auto n = tok.next_integer();
    if (!n) return std::unexpected(n.error());
    e.n = *n;

    e.entries.reserve(e.n);
    for (int i = 0; i < e.n; ++i) {
        auto v = tok.next_integer();
        if (!v) return std::unexpected(v.error());
        e.entries.push_back(*v);
    }

    return e;
}

} // namespace iges
