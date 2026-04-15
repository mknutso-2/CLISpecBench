// iges::Lexer — Full implementation.
// Splits IGES fixed-format lines into SectionLine values.

#include "lexer.hpp"
#include <sstream>
#include <algorithm>

namespace iges {

static Diagnostic make_diag(int line, SectionKind kind,
                            std::string msg, std::string spec_ref) {
    return Diagnostic{Diagnostic::Severity::Error, line, kind,
                      std::move(msg), std::move(spec_ref)};
}

bool Lexer::is_section_code(char c) {
    switch (c) {
        case 'S': case 'G': case 'D': case 'P': case 'T': case 'C':
            return true;
        default:
            return false;
    }
}

std::expected<SectionLine, Diagnostic>
Lexer::parse_line(std::string_view raw_line, int file_line_number) {
    // Pad or truncate to 80 columns
    std::string line(raw_line);
    if (line.size() < 80) {
        line.resize(80, ' ');
    }

    // Column 73 (0-indexed: 72) is the section letter code
    char section_char = line[72];
    if (!is_section_code(section_char)) {
        return std::unexpected(make_diag(file_line_number, SectionKind::Start,
            std::string("invalid section code: ") + section_char, "§2.2.1"));
    }

    SectionKind kind = static_cast<SectionKind>(section_char);

    // Columns 74-80 (0-indexed: 73-79) contain the sequence number
    auto seq_str = std::string_view(line).substr(73, 7);
    // Trim leading spaces and parse
    auto first_nonspace = seq_str.find_first_not_of(' ');
    int seq_num = 0;
    if (first_nonspace != std::string_view::npos) {
        auto trimmed = seq_str.substr(first_nonspace);
        for (char c : trimmed) {
            if (c >= '0' && c <= '9') {
                seq_num = seq_num * 10 + (c - '0');
            } else if (c != ' ') {
                return std::unexpected(make_diag(file_line_number, kind,
                    "non-digit in sequence number", "§2.2.1"));
            }
        }
    }

    // Extract data field
    std::string data;
    if (kind == SectionKind::Parameter) {
        // PD lines: columns 1-64 (0-indexed: 0-63)
        data = line.substr(0, 64);
    } else {
        // All other sections: columns 1-72 (0-indexed: 0-71)
        data = line.substr(0, 72);
    }

    // §2.2.4.2: Start section data shall not contain control characters
    if (kind == SectionKind::Start) {
        for (char c : data) {
            if ((c >= '\x00' && c <= '\x1F') || c == '\x7F') {
                return std::unexpected(make_diag(file_line_number, kind,
                    "control character in Start section data", "§2.2.4.2"));
            }
        }
    }

    return SectionLine{kind, seq_num, std::move(data)};
}

std::expected<std::vector<SectionLine>, DiagList>
Lexer::read_all(std::istream& input) {
    std::vector<SectionLine> lines;
    DiagList errors;
    std::string raw_line;
    int line_num = 0;
    bool has_start = false;

    while (std::getline(input, raw_line)) {
        ++line_num;
        // Strip trailing CR if present (CRLF files)
        if (!raw_line.empty() && raw_line.back() == '\r') {
            raw_line.pop_back();
        }
        // Skip completely blank lines
        if (raw_line.empty()) continue;
        // Pad to 80 if needed
        if (raw_line.size() < 80) raw_line.resize(80, ' ');

        auto result = parse_line(raw_line, line_num);
        if (!result.has_value()) {
            errors.push_back(result.error());
            continue;
        }
        if (result.value().kind == SectionKind::Start) has_start = true;
        lines.push_back(std::move(result.value()));
    }

    // §2.2.4.2: At least one Start Section line shall appear
    if (!has_start) {
        errors.push_back(make_diag(0, SectionKind::Start,
            "no Start section lines found", "§2.2.4.2"));
    }

    if (!errors.empty()) {
        return std::unexpected(std::move(errors));
    }

    return lines;
}

} // namespace iges
