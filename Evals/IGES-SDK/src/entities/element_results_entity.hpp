#pragma once
// iges::ElementResultsEntity — Type 148.
//
// §4.36: "The number of results data values depends upon: (1) NV,
// the number of results data values per ECO630 reporting location;
// (2) NRL, the number of results data reporting locations in a FEM
// element per layer; and (3) NL, the number of layers in the FEM
// element."
//
// Per element: EN, EP, ITOP, NL, DLF, NRL, RDRL(1..NRL), NUMV, V(1..NUMV)
// where NUMV = NV * NL * NRL, and V is column-major: J(1..NV), K(1..NL), L(1..NRL).

#include "entity.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct ElementResultsElement {
    int en = 0;                        // FEM element number identifier
    DEIndex ep{0};                     // Pointer to the DE of the FEM Element Entity
    int itop = 0;                      // Element Topology type
    int nl = 0;                        // Number of layers per results data report location
    int dlf = 0;                       // Data Layer Flag (0..4)
    int nrl = 0;                       // Number of results data report locations
    std::vector<int> rdrl;             // Results data report locations (NRL values)
    int numv = 0;                      // Total number of result values (NV*NL*NRL)
    std::vector<Real> values;          // Result values V(J,K,L) in column-major order
};

struct ElementResultsEntity {
    DEIndex gnote{0};                  // Pointer to General Note Entity
    int scn = 0;                       // Analysis subcase number (0 = no subcase)
    Real time = 0.0;                   // Analysis time value
    int nv = 0;                        // Number of results values per report location
    int rrf = 0;                       // Results Reporting Flag (0..3)
    int ne = 0;                        // Number of FEM elements
    std::vector<ElementResultsElement> elements;
};

std::expected<ElementResultsEntity, Diagnostic>
parse_element_results_entity(ParamTokenizer& tok);

} // namespace iges
