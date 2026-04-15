#pragma once
// iges::validate — Structural validation of an IgesFile.
//
// Checks cross-references (DE pointers), entity-type constraints,
// and global section invariants. Returns a list of diagnostics;
// empty list means the file is valid.

#include "../parser/file_reader.hpp"
#include "../types.hpp"
#include <vector>

namespace iges {

// Validate structural integrity of a parsed IGES file.
// Returns diagnostics for any issues found. An empty list means valid.
DiagList validate(IgesFile const& file);

} // namespace iges
