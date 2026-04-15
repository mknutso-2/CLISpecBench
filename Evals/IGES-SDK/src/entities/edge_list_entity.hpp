#pragma once
// iges::EdgeListEntity — Type 504, Form 1.
//
// §4.144.1: "The Edge List Entity models an edge or a list of edges."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct EdgeTuple {
    DEIndex curve;             // Model space curve pointer
    DEIndex svp;               // Start vertex list pointer
    int sv = 0;                // Start vertex index
    DEIndex tvp;               // Terminate vertex list pointer
    int tv = 0;                // Terminate vertex index
};

struct EdgeListEntity {
    int n = 0;
    std::vector<EdgeTuple> edges;
};

std::expected<EdgeListEntity, Diagnostic>
parse_edge_list_entity(ParamTokenizer& tok);

} // namespace iges
