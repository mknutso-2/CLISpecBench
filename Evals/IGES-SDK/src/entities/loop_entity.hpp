#pragma once
// iges::LoopEntity — Type 508, Form 1.
//
// §4.145: "The Loop Entity specifies a bound of a face."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct ParamSpaceCurve {
    bool isoparametric = false;
    DEIndex curve;
};

struct EdgeUse {
    int type = 0;              // 0=Edge, 1=Vertex
    DEIndex edge;              // Pointer to Edge/Vertex List
    int ndx = 0;               // List index
    bool orientation = true;   // Orientation flag
    int k = 0;                 // Number of param space curves
    std::vector<ParamSpaceCurve> param_curves;
};

struct LoopEntity {
    int n = 0;
    std::vector<EdgeUse> edge_uses;
};

std::expected<LoopEntity, Diagnostic>
parse_loop_entity(ParamTokenizer& tok);

} // namespace iges
