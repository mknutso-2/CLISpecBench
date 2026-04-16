#pragma once
// iges::writer — Low-level formatting utilities for IGES file output.
//
// Implements the encoding rules from §2.2.2 (field types) and
// §2.2.4 (section line layout).

#include "../types.hpp"
#include <string>

namespace iges {

// ── Field formatters (§2.2.2) ───────────────────────────────────

// §2.2.2.3: Hollerith encoding: "hello" → "5Hhello"
std::string format_hollerith(std::string_view s);

// §2.2.2.1: Integer encoding
std::string format_integer(int v);

// §2.2.2.2: Real encoding — compact decimal representation
std::string format_real(Real v);

// §2.2.2.4: Pointer encoding (DEIndex → integer string)
std::string format_pointer(DEIndex idx);

// §2.2.2.6: Logical encoding: true → "1", false → "0"
std::string format_logical(bool v);

// ── Line formatters (§2.2.4) ────────────────────────────────────

// Format a general section line (S, G): cols 1-72 data, col 73 section letter,
// cols 74-80 sequence number. Returns exactly 80 characters.
std::string format_section_line(std::string_view data, SectionKind kind, int seq);

// Format a parameter data line: cols 1-64 data, col 65 space,
// cols 66-72 DE back-pointer, col 73 'P', cols 74-80 sequence.
std::string format_pd_line(std::string_view data, int de_seq, int pd_seq);

// Format the terminate line: S count, G count, D count, P count.
std::string format_terminate_line(int s_count, int g_count, int d_count, int p_count);

// ── Directory Entry line formatter (§2.2.4.4) ──────────────────

struct DirectoryEntry;  // forward decl

// Format a DirectoryEntry into two 80-column lines (DE pair).
// de_seq is the sequence number for the first line (must be odd).
std::string format_directory_entry(DirectoryEntry const& de, int de_seq);

// ── PD line splitting (§2.2.4.5) ───────────────────────────────

// Split a free-format PD string into 64-column chunks and format
// as PD lines with DE back-pointer. Returns the formatted lines
// concatenated and the number of PD lines produced.
struct PdSplitResult {
    std::string lines;
    int line_count = 0;
};

PdSplitResult split_pd_lines(std::string_view pd_string, int entity_type,
                              int de_seq, int& pd_seq_counter,
                              char param_delimiter = ',');

} // namespace iges
