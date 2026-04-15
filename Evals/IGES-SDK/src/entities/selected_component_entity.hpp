#pragma once
// iges::SelectedComponentEntity — Type 182.
//
// §4.47: "The Selected Component Entity provides a means of selecting
//   one component of a disjoint CSG solid."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>

namespace iges {

struct SelectedComponentEntity {
    DEIndex btree;             // Pointer to Boolean Tree Entity
    Vec3 sel_point;            // Point in or on desired component
};

std::expected<SelectedComponentEntity, Diagnostic>
parse_selected_component_entity(ParamTokenizer& tok);

} // namespace iges
