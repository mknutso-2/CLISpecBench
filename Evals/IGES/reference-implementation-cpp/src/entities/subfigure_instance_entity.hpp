#pragma once
// iges::SubfigureInstanceEntity — Type 408.
//
// §4.133: "A Singular Subfigure Instance Entity specifies an
//   occurrence of a single instance of a defined subfigure."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>

namespace iges {

struct SubfigureInstanceEntity {
    DEIndex de;
    Vec3 translation;
    Real scale = 1.0;
};

std::expected<SubfigureInstanceEntity, Diagnostic>
parse_subfigure_instance_entity(ParamTokenizer& tok);

} // namespace iges
