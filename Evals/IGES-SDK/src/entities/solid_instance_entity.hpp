#pragma once
// iges::SolidInstanceEntity — Type 430.
//
// §4.142: "The Solid Instance Entity provides a mechanism for
//   replicating a solid representation."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct SolidInstanceEntity {
    DEIndex ptr;               // Pointer to the solid
};

std::expected<SolidInstanceEntity, Diagnostic>
parse_solid_instance_entity(ParamTokenizer& tok);

} // namespace iges
