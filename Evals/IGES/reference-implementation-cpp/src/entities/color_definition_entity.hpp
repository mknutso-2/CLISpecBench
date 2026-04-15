#pragma once
// iges::ColorDefinitionEntity — Type 314.
//
// §4.93: "The Color Definition Entity is used to communicate the
//   relationship of a color value to the color."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <string>

namespace iges {

struct ColorDefinitionEntity {
    Real red = 0.0;
    Real green = 0.0;
    Real blue = 0.0;
    std::string name;
};

std::expected<ColorDefinitionEntity, Diagnostic>
parse_color_definition_entity(ParamTokenizer& tok);

} // namespace iges
