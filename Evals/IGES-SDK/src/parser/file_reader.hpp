#pragma once
// iges::IgesFile — Parse a complete IGES file from a stream.
//
// Uses the Lexer to split into section lines, then parses:
//   - Start section (human-readable comments)
//   - Global section (26-field metadata)
//   - Directory entries (pairs of 80-column DE lines)
//   - Parameter data (concatenated PD lines per entity, keyed by DE)

#include "../types.hpp"
#include "../model/global_section.hpp"
#include "../model/directory_entry.hpp"
#include <string>
#include <vector>
#include <expected>
#include <istream>

namespace iges {

// One entity's raw data as extracted from the file.
struct RawEntity {
    DirectoryEntry de;
    std::string pd_string;  // Concatenated PD data for this entity
};

// The result of parsing a complete IGES file.
struct IgesFile {
    std::vector<std::string> start_lines;  // Human-readable start section
    GlobalSection global;
    std::vector<RawEntity> entities;
};

// Parse a complete IGES file from an input stream.
std::expected<IgesFile, DiagList>
read_iges_file(std::istream& input);

} // namespace iges
