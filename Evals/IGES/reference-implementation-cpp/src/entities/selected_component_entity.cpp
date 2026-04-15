// iges::SelectedComponentEntity — Full implementation.

#include "selected_component_entity.hpp"

namespace iges {

std::expected<SelectedComponentEntity, Diagnostic>
parse_selected_component_entity(ParamTokenizer& tok) {
    SelectedComponentEntity e;

    auto btree = tok.next_pointer();
    if (!btree) return std::unexpected(btree.error());
    e.btree = *btree;

    auto x = tok.next_real(); if (!x) return std::unexpected(x.error()); e.sel_point.x = *x;
    auto y = tok.next_real(); if (!y) return std::unexpected(y.error()); e.sel_point.y = *y;
    auto z = tok.next_real(); if (!z) return std::unexpected(z.error()); e.sel_point.z = *z;

    return e;
}

} // namespace iges
