#pragma once
// iges::GlobalSection — The 26-field Global Section of an IGES file.

#include "../types.hpp"
#include <string>
#include <optional>

namespace iges {

struct GlobalSection {
    // Field 1-2: delimiters
    char            param_delimiter  = ',';
    char            record_delimiter = ';';

    // Field 3-6: identification strings (required, no default)
    std::string     product_id_sender;
    std::string     file_name;
    std::string     native_system_id;
    std::string     preprocessor_version;

    // Field 7-11: numeric precision (required, no default)
    int             integer_bits      = 0;
    int             sp_magnitude      = 0;
    int             sp_significance   = 0;
    int             dp_magnitude      = 0;
    int             dp_significance   = 0;

    // Field 12: product ID for receiver (default = field 3)
    std::string     product_id_receiver;

    // Field 13: model space scale (default 1.0)
    Real            model_space_scale = 1.0;

    // Field 14-15: units
    Units           units      = Units::Inches;
    std::string     units_name = "IN";

    // Field 16-17: line weight
    int             max_line_weight_grads = 1;
    Real            max_line_weight_width = 0.0;

    // Field 18: file generation timestamp (required, no default)
    Timestamp       file_timestamp;

    // Field 19-20: resolution and max coordinate
    Real            min_resolution    = 0.0;
    Real            max_coordinate    = 0.0;

    // Field 21-22: author info
    std::string     author;
    std::string     organization;

    // Field 23-24: standard flags
    SpecVersion     spec_version  = SpecVersion::V3_0;  // default = 3
    DraftingStandard drafting_std = DraftingStandard::None;

    // Field 25: model creation/modification timestamp
    std::optional<Timestamp> model_timestamp;

    // Field 26: application protocol
    std::string     app_protocol;

    bool operator==(GlobalSection const&) const = default;
};

// Parse a GlobalSection from a sequence of free-formatted Global
// section data (columns 1-72 of all G lines, concatenated).
std::expected<GlobalSection, DiagList>
parse_global_section(std::string_view data);

} // namespace iges
