#pragma once
// iges::DirectoryEntry — The 20-field Directory Entry record.

#include "../types.hpp"
#include <string>
#include <expected>

namespace iges {

struct StatusNumber {
    BlankStatus       blank      = BlankStatus::Visible;
    SubordinateSwitch subordinate = SubordinateSwitch::Independent;
    EntityUseFlag     entity_use  = EntityUseFlag::Geometry;
    HierarchyFlag     hierarchy   = HierarchyFlag::GlobalTopDown;

    bool operator==(StatusNumber const&) const = default;
};

struct DirectoryEntry {
    EntityType      entity_type;            // fields 1, 11
    int             param_data_ptr = 0;     // field 2 (PD sequence number)
    int             structure      = 0;     // field 3
    LineFontVariant line_font;              // field 4
    LevelVariant    level;                  // field 5
    DEIndex         view;                   // field 6
    DEIndex         xform_matrix;           // field 7
    DEIndex         label_display;          // field 8
    StatusNumber    status;                 // field 9
    // field 10: sequence number (not stored, derived from position)
    // field 11: same as field 1
    int             line_weight    = 0;     // field 12
    ColorVariant    color;                  // field 13
    int             param_line_count = 0;   // field 14
    FormNumber      form;                   // field 15
    // fields 16, 17: reserved
    std::string     entity_label;           // field 18 (up to 8 chars)
    int             entity_subscript = 0;   // field 19
    // field 20: sequence number (derived)

    bool operator==(DirectoryEntry const&) const = default;
};

// Parse a DE record from two 80-column lines (160 chars total).
std::expected<DirectoryEntry, Diagnostic>
parse_directory_entry(std::string_view line1, std::string_view line2,
                      int file_line_number);

// Parse the 8-digit status number into its 4 sub-fields.
std::expected<StatusNumber, Diagnostic>
parse_status_number(std::string_view eight_chars);

// Format a StatusNumber back into 8 characters.
std::string format_status_number(StatusNumber const& s);

} // namespace iges
