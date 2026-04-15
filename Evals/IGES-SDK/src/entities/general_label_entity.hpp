#pragma once
// iges::GeneralLabelEntity — Type 210.
//
// §4.57: "A General Label Entity consists of a general note with
//   zero or more associated leaders."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <vector>

namespace iges {

struct GeneralLabelEntity {
    DEIndex denote;
    int n = 0;
    std::vector<DEIndex> leaders;
};

std::expected<GeneralLabelEntity, Diagnostic>
parse_general_label_entity(ParamTokenizer& tok);

} // namespace iges
