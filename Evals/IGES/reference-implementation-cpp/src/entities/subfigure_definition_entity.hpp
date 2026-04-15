#pragma once
// iges::SubfigureDefinitionEntity — Type 308.
//
// §4.92: "A Subfigure Definition Entity permits a single definition
//   of a detail to be utilized in multiple instances."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <string>
#include <vector>

namespace iges {

struct SubfigureDefinitionEntity {
    int depth = 0;
    std::string name;
    int n = 0;
    std::vector<DEIndex> entities;
};

std::expected<SubfigureDefinitionEntity, Diagnostic>
parse_subfigure_definition_entity(ParamTokenizer& tok);

} // namespace iges
