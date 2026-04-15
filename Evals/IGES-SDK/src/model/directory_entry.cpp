// iges::DirectoryEntry — Full implementation.
// Parses §2.2.4.4 Directory Entry records and §2.2.4.4.9 Status Number.

#include "directory_entry.hpp"
#include <cstdio>

namespace iges {

static Diagnostic make_diag(int line, std::string msg, std::string spec_ref) {
    return Diagnostic{Diagnostic::Severity::Error, line,
                      SectionKind::Directory, std::move(msg), std::move(spec_ref)};
}

// §2.2.4.4.9 — Parse the 8-digit status number "BBSSEEUU"
// BB = blank status (2 digits), SS = subordinate (2 digits),
// EE = entity use (2 digits), UU = hierarchy (2 digits)
std::expected<StatusNumber, Diagnostic>
parse_status_number(std::string_view eight_chars) {
    if (eight_chars.size() < 8) {
        return std::unexpected(make_diag(0, "status number too short", "§2.2.4.4.9"));
    }

    auto parse_2digit = [](std::string_view sv) -> int {
        int d0 = (sv[0] == ' ') ? 0 : (sv[0] - '0');
        int d1 = (sv[1] == ' ') ? 0 : (sv[1] - '0');
        return d0 * 10 + d1;
    };

    int blank_val = parse_2digit(eight_chars.substr(0, 2));
    int sub_val   = parse_2digit(eight_chars.substr(2, 2));
    int use_val   = parse_2digit(eight_chars.substr(4, 2));
    int hier_val  = parse_2digit(eight_chars.substr(6, 2));

    StatusNumber sn;
    sn.blank      = static_cast<BlankStatus>(blank_val);
    sn.subordinate = static_cast<SubordinateSwitch>(sub_val);
    sn.entity_use  = static_cast<EntityUseFlag>(use_val);
    sn.hierarchy   = static_cast<HierarchyFlag>(hier_val);

    return sn;
}

// §2.2.4.4.9 — Format a StatusNumber back to 8 chars "BBSSEEUU"
std::string format_status_number(StatusNumber const& s) {
    char buf[9];
    std::snprintf(buf, sizeof(buf), "%02d%02d%02d%02d",
                  static_cast<int>(s.blank),
                  static_cast<int>(s.subordinate),
                  static_cast<int>(s.entity_use),
                  static_cast<int>(s.hierarchy));
    return std::string(buf, 8);
}

// Parse an 8-char right-justified integer field from a DE line
static int parse_de_int(std::string_view field) {
    // Trim spaces
    auto start = field.find_first_not_of(' ');
    if (start == std::string_view::npos) return 0; // defaulted
    auto end = field.find_last_not_of(' ');
    auto trimmed = field.substr(start, end - start + 1);

    int sign = 1;
    std::size_t i = 0;
    if (trimmed[0] == '-') { sign = -1; i = 1; }
    else if (trimmed[0] == '+') { i = 1; }

    int val = 0;
    for (; i < trimmed.size(); ++i) {
        if (trimmed[i] >= '0' && trimmed[i] <= '9') {
            val = val * 10 + (trimmed[i] - '0');
        }
    }
    return sign * val;
}

// Parse a DE record from two 80-column lines.
std::expected<DirectoryEntry, Diagnostic>
parse_directory_entry(std::string_view line1, std::string_view line2,
                      int file_line_number) {
    if (line1.size() < 72 || line2.size() < 72) {
        return std::unexpected(make_diag(file_line_number,
            "DE lines too short", "§2.2.4.4"));
    }

    DirectoryEntry de;

    // Line 1 fields (each 8 chars): 1-8, 9-16, 17-24, 25-32, 33-40, 41-48, 49-56, 57-64, 65-72
    de.entity_type     = EntityType{parse_de_int(line1.substr(0, 8))};
    de.param_data_ptr  = parse_de_int(line1.substr(8, 8));
    de.structure       = parse_de_int(line1.substr(16, 8));
    de.line_font.raw   = parse_de_int(line1.substr(24, 8));
    de.level.raw       = parse_de_int(line1.substr(32, 8));
    de.view            = DEIndex{parse_de_int(line1.substr(40, 8))};
    de.xform_matrix    = DEIndex{parse_de_int(line1.substr(48, 8))};
    de.label_display   = DEIndex{parse_de_int(line1.substr(56, 8))};

    // Field 9: status number (cols 65-72 of line 1)
    auto status_result = parse_status_number(line1.substr(64, 8));
    if (status_result.has_value()) {
        de.status = status_result.value();
    }

    // Line 2 fields: entity_type (repeat), line_weight, color, param_line_count,
    //   form, reserved, reserved, entity_label, entity_subscript
    // field 11 = entity type (same as field 1, skip)
    de.line_weight     = parse_de_int(line2.substr(8, 8));
    de.color.raw       = parse_de_int(line2.substr(16, 8));
    de.param_line_count = parse_de_int(line2.substr(24, 8));
    de.form            = FormNumber{parse_de_int(line2.substr(32, 8))};
    // fields 16, 17: reserved (skip)
    // field 18: entity label (cols 57-64 of line 2, plain string)
    auto label = line2.substr(56, 8);
    // Trim trailing spaces
    auto label_end = label.find_last_not_of(' ');
    if (label_end != std::string_view::npos) {
        de.entity_label = std::string(label.substr(0, label_end + 1));
    }
    de.entity_subscript = parse_de_int(line2.substr(64, 8));

    return de;
}

} // namespace iges
