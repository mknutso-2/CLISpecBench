#pragma once
// iges::ExternalReferenceEntity — Type 416.
//
// §4.135: "An External Reference Entity provides a link between
//   entities in separate IGES files."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include <expected>
#include <string>

namespace iges {

struct ExternalReferenceEntity {
    std::string filename;
    std::string entity_name;
};

std::expected<ExternalReferenceEntity, Diagnostic>
parse_external_reference_entity(ParamTokenizer& tok, int form);

} // namespace iges
