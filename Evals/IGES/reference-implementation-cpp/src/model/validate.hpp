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

// Validate the portion of an IgesFile that applies to `iges write`
// input: Global section field invariants plus per-entity DE metadata
// that is carried through verbatim from caller JSON (entity_type sign,
// view / xform_matrix / label_display cross-references). The
// param_line_count and pd_string.empty() checks are skipped because
// the write path re-derives param_line_count from the PD layout and
// always builds a non-empty pd_string. TR §1.2 requires the write
// path to reject the same inputs the parse path would reject.
DiagList validate_write_input(IgesFile const& file);

} // namespace iges
