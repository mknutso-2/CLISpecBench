#pragma once
// iges::UnitsDataEntity — Type 316.
//
// §4.77: "The Units Data Entity stores data about the model units
//   used in the file."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <string>
#include <vector>

namespace iges {

struct UnitEntry {
    std::string typ;   // Unit type name (e.g. "LENGTH")
    std::string val;   // Unit value (e.g. "MM")
    Real sf = 0.0;     // Scale factor
};

struct UnitsDataEntity {
    int np = 0;        // Number of units
    std::vector<UnitEntry> units;
};

std::expected<UnitsDataEntity, Diagnostic>
parse_units_data_entity(ParamTokenizer& tok);

} // namespace iges
