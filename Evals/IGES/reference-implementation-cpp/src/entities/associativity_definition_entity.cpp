// iges::AssociativityDefinitionEntity — Full implementation.

#include "associativity_definition_entity.hpp"

namespace iges {

std::expected<AssociativityDefinitionEntity, Diagnostic>
parse_associativity_definition_entity(ParamTokenizer& tok) {
    AssociativityDefinitionEntity e;

    auto k = tok.next_integer(); if (!k) return std::unexpected(k.error()); e.k = *k;

    e.classes.reserve(e.k);
    for (int i = 0; i < e.k; ++i) {
        AssociativityClass cls;

        auto bp = tok.next_integer(); if (!bp) return std::unexpected(bp.error()); cls.bp = *bp;
        auto or_ = tok.next_integer(); if (!or_) return std::unexpected(or_.error()); cls.order = *or_;
        auto n = tok.next_integer(); if (!n) return std::unexpected(n.error()); cls.n = *n;

        cls.item_types.reserve(cls.n);
        for (int j = 0; j < cls.n; ++j) {
            auto it = tok.next_integer(); if (!it) return std::unexpected(it.error());
            cls.item_types.push_back(*it);
        }

        e.classes.push_back(std::move(cls));
    }

    return e;
}

} // namespace iges
