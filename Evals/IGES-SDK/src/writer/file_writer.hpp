#pragma once
// iges::write_iges_file — Assemble a complete IGES file from its parts.
//
// Implements the writer pipeline from ARCHITECTURE.md §7:
//   1. Emit Start section
//   2. Serialize GlobalSection
//   3. For each entity: PD lines + DE pair
//   4. Emit Terminate section
//   5. Sequence numbers recomputed from scratch

#include "../model/global_section.hpp"
#include "../model/directory_entry.hpp"
#include <string>
#include <vector>

namespace iges {

// One entity ready for writing: its DE metadata and already-serialized PD string.
struct WritableEntity {
    DirectoryEntry de;
    std::string pd_string;  // Free-format, semicolon-terminated (e.g. "1.0,2.0;")
};

// Write a complete IGES file to a string.
// start_lines: content for the Start section (one string per line, max 72 chars each).
// global: the GlobalSection to serialize.
// entities: the entities with their DE metadata and PD strings.
std::string write_iges_file(
    std::vector<std::string> const& start_lines,
    GlobalSection const& global,
    std::vector<WritableEntity> const& entities);

} // namespace iges
