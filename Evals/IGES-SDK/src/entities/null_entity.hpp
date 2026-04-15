#pragma once
// iges::NullEntity — Type 0.
//
// §4.1: "A Null Entity is used when an application requires an
//   entity type number but the entity itself has no significance."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>

namespace iges {

struct NullEntity {};

std::expected<NullEntity, Diagnostic>
parse_null_entity(ParamTokenizer& tok);

} // namespace iges
