#pragma once
// iges::PropertyEntity — Type 406.
//
// §4.97: "The Property Entity ... is used to store application-specific
//   property data associated with other entities."
// The form number determines interpretation; we store raw FieldValues.

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct PropertyEntity {
    int np = 0;
    std::vector<FieldValue> values;
};

std::expected<PropertyEntity, Diagnostic>
parse_property_entity(ParamTokenizer& tok);

} // namespace iges
