#pragma once
// iges::AttributeTableDefinitionEntity — Type 322.
//
// §4.79: "The Attribute Table Definition Entity supports the concept of
//   a well-defined collection of attributes."
//
// Three forms:
//   Form 0: definition only (name, type, count per attribute)
//   Form 1: definition + values
//   Form 2: definition + values + Text Display Template pointers

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <string>
#include <variant>
#include <vector>

namespace iges {

// An attribute value — type determined by AVDT field.
//   AVDT 1,6 → int;  AVDT 2 → Real;  AVDT 3 → std::string;  AVDT 4 → DEIndex
using AttributeValue = std::variant<int, Real, std::string, DEIndex>;

struct AttributeEntry {
    int at = 0;                          // Attribute type number
    int avdt = 0;                        // Attribute value data type (0-6)
    int avc = 0;                         // Attribute value count
    std::vector<AttributeValue> values;  // AVC values (Forms 1, 2 only)
    std::vector<DEIndex> display_ptrs;   // AVC display template pointers (Form 2 only)
};

struct AttributeTableDefinitionEntity {
    std::string name;                    // NAME — table name
    int alt = 0;                         // ALT — attribute list type
    int na = 0;                          // NA — number of attributes
    std::vector<AttributeEntry> attributes;
};

std::expected<AttributeTableDefinitionEntity, Diagnostic>
parse_attribute_table_definition_entity(ParamTokenizer& tok, int form);

} // namespace iges
