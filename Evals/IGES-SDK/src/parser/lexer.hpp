#pragma once
// iges::Lexer — Line-level reader for IGES fixed-format files.
//
// Splits an input stream into 80-column records, identifies section
// letter codes, validates sequence numbers, and produces SectionLine
// values for downstream consumption.

#include "../types.hpp"
#include <string>
#include <string_view>
#include <vector>
#include <expected>
#include <istream>

namespace iges {

// ── SectionLine ──────────────────────────────────────────────
// One 80-column line from an IGES file, decomposed.
struct SectionLine {
    SectionKind kind;
    int         sequence_number;    // cols 74-80
    std::string data;               // cols 1-72 (or 1-64 for PD)
};

// ── Lexer ────────────────────────────────────────────────────
class Lexer {
public:
    // Read all lines from an input stream and decompose them.
    // Returns lines grouped by section in file order.
    static std::expected<std::vector<SectionLine>, DiagList>
    read_all(std::istream& input);

    // Parse a single 80-column line (or longer line, truncated/padded).
    static std::expected<SectionLine, Diagnostic>
    parse_line(std::string_view raw_line, int file_line_number);

    // Validate that a character is a valid section letter code.
    static bool is_section_code(char c);
};

} // namespace iges
