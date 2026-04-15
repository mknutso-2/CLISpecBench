#pragma once
// iges::NodalResultsEntity — Type 146.
//
// §4.35: "The number of analysis results data values per FEM node and
// their physical interpretation depends upon specified values of the
// form number (TYPE) and NV."
// Parameters: GNOTE, SCN, TIME, NV, NN, {NODE, NP, V(1..NV)} x NN

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct NodalResultsNode {
    int node_id = 0;            // FEM node number identifier
    DEIndex np{0};              // Pointer to the DE of the Node Entity
    std::vector<Real> values;   // NV data values for this node
};

struct NodalResultsEntity {
    DEIndex gnote{0};           // Pointer to General Note Entity
    int scn = 0;                // Analysis subcase number (0 = no subcase)
    Real time = 0.0;            // Analysis time value
    int nv = 0;                 // Number of real values per node
    int nn = 0;                 // Number of FEM nodes
    std::vector<NodalResultsNode> nodes;
};

std::expected<NodalResultsEntity, Diagnostic>
parse_nodal_results_entity(ParamTokenizer& tok);

} // namespace iges
