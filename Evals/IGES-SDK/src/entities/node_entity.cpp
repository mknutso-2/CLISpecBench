// iges::NodeEntity — Full implementation.

#include "node_entity.hpp"

namespace iges {

std::expected<NodeEntity, Diagnostic>
parse_node_entity(ParamTokenizer& tok) {
    NodeEntity e;

    auto x = tok.next_real(); if (!x) return std::unexpected(x.error()); e.x = *x;
    auto y = tok.next_real(); if (!y) return std::unexpected(y.error()); e.y = *y;
    auto z = tok.next_real(); if (!z) return std::unexpected(z.error()); e.z = *z;

    auto ndcsp = tok.next_integer_or(0);
    if (ndcsp) e.ndcsp = DEIndex{*ndcsp};

    return e;
}

} // namespace iges
