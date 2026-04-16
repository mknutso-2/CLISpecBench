// iges::writer — Formatting utility implementations.

#include "format.hpp"
#include "../model/directory_entry.hpp"
#include <cstdio>
#include <cstring>
#include <format>

namespace iges {

// ── Field formatters ────────────────────────────────────────────

std::string format_hollerith(std::string_view s) {
    if (s.empty()) return "";
    return std::format("{}H{}", s.size(), s);
}

std::string format_integer(int v) {
    return std::to_string(v);
}

std::string format_real(Real v) {
    // Use compact representation, always include decimal point
    char buf[64];
    std::snprintf(buf, sizeof(buf), "%.15g", v);
    std::string result(buf);
    // Ensure there's a decimal point (distinguish from integer)
    if (result.find('.') == std::string::npos &&
        result.find('e') == std::string::npos &&
        result.find('E') == std::string::npos) {
        result += ".0";
    }
    return result;
}

std::string format_pointer(DEIndex idx) {
    return std::to_string(idx.value);
}

std::string format_logical(bool v) {
    return v ? "1" : "0";
}

// ── Line formatters ─────────────────────────────────────────────

static char section_char(SectionKind kind) {
    return static_cast<char>(kind);
}

std::string format_section_line(std::string_view data, SectionKind kind, int seq) {
    // Cols 1-72: data (left-justified, padded with spaces)
    // Col  73:   section letter
    // Cols 74-80: sequence number (right-justified)
    std::string line(80, ' ');
    auto copy_len = std::min(data.size(), static_cast<std::size_t>(72));
    std::memcpy(line.data(), data.data(), copy_len);
    line[72] = section_char(kind);
    auto seq_str = std::format("{:>7}", seq);
    std::memcpy(line.data() + 73, seq_str.data(), 7);
    return line;
}

std::string format_pd_line(std::string_view data, int de_seq, int pd_seq) {
    // Cols 1-64:  data (left-justified, padded with spaces)
    // Col  65:    space
    // Cols 66-72: DE back-pointer (right-justified)
    // Col  73:    'P'
    // Cols 74-80: sequence number (right-justified)
    std::string line(80, ' ');
    auto copy_len = std::min(data.size(), static_cast<std::size_t>(64));
    std::memcpy(line.data(), data.data(), copy_len);
    line[64] = ' ';
    auto de_str = std::format("{:>7}", de_seq);
    std::memcpy(line.data() + 65, de_str.data(), 7);
    line[72] = 'P';
    auto seq_str = std::format("{:>7}", pd_seq);
    std::memcpy(line.data() + 73, seq_str.data(), 7);
    return line;
}

std::string format_terminate_line(int s_count, int g_count, int d_count, int p_count) {
    // §2.2.4.6: Terminate section: one line
    // Cols 1-8:  "S" + right-justified count (7 chars)
    // Cols 9-16: "G" + right-justified count
    // Cols 17-24: "D" + right-justified count
    // Cols 25-32: "P" + right-justified count
    // Cols 33-72: spaces
    // Col  73:   'T'
    // Cols 74-80: "      1"
    std::string line(80, ' ');
    auto s_str = std::format("S{:>7}", s_count);
    auto g_str = std::format("G{:>7}", g_count);
    auto d_str = std::format("D{:>7}", d_count);
    auto p_str = std::format("P{:>7}", p_count);
    std::memcpy(line.data() + 0,  s_str.data(), 8);
    std::memcpy(line.data() + 8,  g_str.data(), 8);
    std::memcpy(line.data() + 16, d_str.data(), 8);
    std::memcpy(line.data() + 24, p_str.data(), 8);
    line[72] = 'T';
    std::memcpy(line.data() + 73, "      1", 7);
    return line;
}

// ── Directory Entry formatter (§2.2.4.4) ────────────────────────

std::string format_directory_entry(DirectoryEntry const& de, int de_seq) {
    // Line 1: fields 1-9 (each 8 chars) + col 73 'D' + cols 74-80 seq
    std::string line1(80, ' ');
    auto put_field = [](std::string& line, int col0, std::string_view val) {
        // Right-justify val in 8-char field starting at col0 (0-based)
        auto len = std::min(val.size(), static_cast<std::size_t>(8));
        auto offset = col0 + 8 - len;
        std::memcpy(line.data() + offset, val.data(), len);
    };

    put_field(line1, 0,  std::format("{}", de.entity_type.value));   // field 1
    put_field(line1, 8,  std::format("{}", de.param_data_ptr));       // field 2
    put_field(line1, 16, std::format("{}", de.structure));             // field 3
    put_field(line1, 24, std::format("{}", de.line_font.raw));        // field 4
    put_field(line1, 32, std::format("{}", de.level.raw));            // field 5
    put_field(line1, 40, std::format("{}", de.view.value));           // field 6
    put_field(line1, 48, std::format("{}", de.xform_matrix.value));   // field 7
    put_field(line1, 56, std::format("{}", de.label_display.value));  // field 8

    // Field 9: status number (8 chars, left-justified in its field)
    auto status_str = format_status_number(de.status);
    std::memcpy(line1.data() + 64, status_str.data(), 8);

    line1[72] = 'D';
    auto seq1_str = std::format("{:>7}", de_seq);
    std::memcpy(line1.data() + 73, seq1_str.data(), 7);

    // Line 2: fields 11-19 (each 8 chars) + col 73 'D' + cols 74-80 seq+1
    std::string line2(80, ' ');
    put_field(line2, 0,  std::format("{}", de.entity_type.value));   // field 11 = field 1
    put_field(line2, 8,  std::format("{}", de.line_weight));          // field 12
    put_field(line2, 16, std::format("{}", de.color.raw));            // field 13
    put_field(line2, 24, std::format("{}", de.param_line_count));     // field 14
    put_field(line2, 32, std::format("{}", de.form.value));           // field 15
    // Fields 16, 17: reserved (blank)
    // Field 18: entity label (left-justified, up to 8 chars)
    auto label_len = std::min(de.entity_label.size(), static_cast<std::size_t>(8));
    std::memcpy(line2.data() + 56, de.entity_label.data(), label_len);
    put_field(line2, 64, std::format("{}", de.entity_subscript));    // field 19

    line2[72] = 'D';
    auto seq2_str = std::format("{:>7}", de_seq + 1);
    std::memcpy(line2.data() + 73, seq2_str.data(), 7);

    return line1 + "\n" + line2 + "\n";
}

// ── PD line splitting (§2.2.4.5) ────────────────────────────────

PdSplitResult split_pd_lines(std::string_view pd_string, int entity_type,
                              int de_seq, int& pd_seq_counter,
                              char param_delimiter) {
    // Prepend entity type number + delimiter to the PD string
    std::string full = std::format("{}{}", entity_type, param_delimiter) +
                       std::string(pd_string);

    PdSplitResult result;
    std::size_t pos = 0;
    while (pos < full.size()) {
        auto chunk_len = std::min(static_cast<std::size_t>(64), full.size() - pos);
        auto chunk = full.substr(pos, chunk_len);
        result.lines += format_pd_line(chunk, de_seq, pd_seq_counter);
        result.lines += '\n';
        ++pd_seq_counter;
        ++result.line_count;
        pos += chunk_len;
    }
    // Handle empty PD string edge case
    if (full.empty()) {
        result.lines += format_pd_line("", de_seq, pd_seq_counter);
        result.lines += '\n';
        ++pd_seq_counter;
        ++result.line_count;
    }
    return result;
}

} // namespace iges
