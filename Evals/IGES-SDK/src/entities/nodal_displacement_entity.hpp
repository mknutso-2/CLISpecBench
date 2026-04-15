#pragma once
// iges::NodalDisplacementEntity — Type 138.
//
// §4.29: "Contains the incremental displacements and rotations
// (expressed in radians) for each load case and each node in the model."
// Parameters: NC, GP(1..NC), NN, {NO, NP, X,Y,Z,RX,RY,RZ per NC cases} x NN

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct NodalDisplacementValues {
    Real x  = 0.0;   // X-Incr. translation
    Real y  = 0.0;   // Y-Incr. translation
    Real z  = 0.0;   // Z-Incr. translation
    Real rx = 0.0;   // RX-Incr. rotation
    Real ry = 0.0;   // RY-Incr. rotation
    Real rz = 0.0;   // RZ-Incr. rotation
};

struct NodalDisplacementNode {
    int node_id = 0;                             // Node number identifier
    DEIndex np{0};                               // Pointer to the Node Entity
    std::vector<NodalDisplacementValues> cases;  // One per analysis case (NC values)
};

struct NodalDisplacementEntity {
    int nc = 0;                                  // Number of analysis cases
    std::vector<DEIndex> gp;                     // Pointers to General Note entities (NC)
    int nn = 0;                                  // Number of nodes
    std::vector<NodalDisplacementNode> nodes;
};

std::expected<NodalDisplacementEntity, Diagnostic>
parse_nodal_displacement_entity(ParamTokenizer& tok);

} // namespace iges
