#pragma once
// iges::VertexListEntity — Type 502, Form 1.
//
// §4.143.1: "The Vertex List Entity contains one or more vertices."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>
#include <vector>

namespace iges {

struct VertexListEntity {
    int n = 0;
    std::vector<Vec3> vertices;
};

std::expected<VertexListEntity, Diagnostic>
parse_vertex_list_entity(ParamTokenizer& tok);

} // namespace iges
