// Tests for writer formatting utilities.
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "writer/format.hpp"
#include "model/directory_entry.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §2.2.2.3: "A Hollerith constant consists of nH followed by a
//   string of n characters"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("format_hollerith — basic string", "[writer][spec-2.2.2.3]") {
    // §2.2.2.3: "nH followed by n characters"
    CHECK(format_hollerith("hello") == "5Hhello");
}

TEST_CASE("format_hollerith — empty string", "[writer][spec-2.2.2.3]") {
    CHECK(format_hollerith("") == "");
}

TEST_CASE("format_hollerith — single character", "[writer][spec-2.2.2.3]") {
    CHECK(format_hollerith("X") == "1HX");
}

TEST_CASE("format_hollerith — string with spaces", "[writer][spec-2.2.2.3]") {
    // §2.2.2.3: Hollerith includes all characters
    CHECK(format_hollerith("a b") == "3Ha b");
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.1: Integer formatting
// ─────────────────────────────────────────────────────────────────

TEST_CASE("format_integer — positive", "[writer][spec-2.2.2.1]") {
    CHECK(format_integer(42) == "42");
}

TEST_CASE("format_integer — negative", "[writer][spec-2.2.2.1]") {
    CHECK(format_integer(-7) == "-7");
}

TEST_CASE("format_integer — zero", "[writer][spec-2.2.2.1]") {
    CHECK(format_integer(0) == "0");
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.2: Real formatting — compact representation
// ─────────────────────────────────────────────────────────────────

TEST_CASE("format_real — integer-valued doubles", "[writer][spec-2.2.2.2]") {
    // §2.2.2.2: Real numbers may use decimal point notation
    auto s = format_real(1.0);
    // Must contain a decimal point to distinguish from integer
    CHECK(s.find('.') != std::string::npos);
}

TEST_CASE("format_real — fractional value", "[writer][spec-2.2.2.2]") {
    auto s = format_real(3.14);
    CHECK(s.find('.') != std::string::npos);
}

TEST_CASE("format_real — zero", "[writer][spec-2.2.2.2]") {
    auto s = format_real(0.0);
    CHECK(s.find('.') != std::string::npos);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.4: Pointer formatting — just an integer (DE sequence number)
// ─────────────────────────────────────────────────────────────────

TEST_CASE("format_pointer — non-null", "[writer][spec-2.2.2.4]") {
    CHECK(format_pointer(DEIndex{5}) == "5");
}

TEST_CASE("format_pointer — null pointer is 0", "[writer][spec-2.2.2.4]") {
    CHECK(format_pointer(DEIndex{0}) == "0");
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.6: Logical formatting — "0 = FALSE, 1 = TRUE"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("format_logical — true", "[writer][spec-2.2.2.6]") {
    // §2.2.2.6: "1 = TRUE"
    CHECK(format_logical(true) == "1");
}

TEST_CASE("format_logical — false", "[writer][spec-2.2.2.6]") {
    // §2.2.2.6: "0 = FALSE"
    CHECK(format_logical(false) == "0");
}

// ─────────────────────────────────────────────────────────────────
// Line formatting: pack data into 80-column IGES lines
// ─────────────────────────────────────────────────────────────────

TEST_CASE("format_section_line — start section", "[writer]") {
    // §2.2.4.2: Start section lines: cols 1-72 data, col 73 'S', cols 74-80 sequence
    auto line = format_section_line("Test start line content", SectionKind::Start, 1);
    CHECK(line.size() == 80);
    CHECK(line[72] == 'S');
}

TEST_CASE("format_section_line — global section", "[writer]") {
    auto line = format_section_line("1H,,1H;,", SectionKind::Global, 1);
    CHECK(line.size() == 80);
    CHECK(line[72] == 'G');
}

TEST_CASE("format_section_line — parameter data", "[writer]") {
    // §2.2.4.5: PD lines: cols 1-64 data, col 65 space, cols 66-72 DE back-pointer,
    //   col 73 'P', cols 74-80 sequence
    auto line = format_pd_line("110,1.0,2.0,3.0,4.0,5.0,6.0;", 1, 1);
    CHECK(line.size() == 80);
    CHECK(line[64] == ' ');
    CHECK(line[72] == 'P');
}

TEST_CASE("format_section_line -- terminate section", "[writer]") {
    // §2.2.4.6: Terminate line: fixed fields + 'T' + sequence
    auto line = format_terminate_line(3, 2, 10, 5);
    CHECK(line.size() == 80);
    CHECK(line[72] == 'T');
}

// -----------------------------------------------------------------
// Directory Entry formatting (§2.2.4.4)
// -----------------------------------------------------------------

TEST_CASE("format_directory_entry -- basic DE pair", "[writer][spec-2.2.4.4]") {
    // §2.2.4.4: "Each entry occupies two 80-column records"
    DirectoryEntry de;
    de.entity_type = EntityType{110};
    de.param_data_ptr = 1;
    de.form = FormNumber{0};
    de.param_line_count = 1;
    de.entity_label = "LINE";
    de.entity_subscript = 1;

    auto result = format_directory_entry(de, 1);
    // Two 80-char lines + 2 newlines
    CHECK(result.size() == 162);
    // Line 1: col 73 = 'D', cols 74-80 = "      1"
    CHECK(result[72] == 'D');
    // Line 2: col 73 = 'D', cols 74-80 = "      2"
    CHECK(result[81 + 72] == 'D');
}

// -----------------------------------------------------------------
// PD line splitting (§2.2.4.5)
// -----------------------------------------------------------------

TEST_CASE("split_pd_lines -- short PD fits one line", "[writer][spec-2.2.4.5]") {
    // §2.2.4.5: "Parameter data ... in columns 1 through 64"
    int seq = 1;
    auto r = split_pd_lines("1.0,2.0,3.0;", 110, 1, seq);
    CHECK(r.line_count == 1);
    CHECK(seq == 2);
    // Each PD line is 80 chars + newline
    CHECK(r.lines.size() == 81);
    // Check the 'P' at col 73
    CHECK(r.lines[72] == 'P');
}

TEST_CASE("split_pd_lines -- long PD splits across lines", "[writer][spec-2.2.4.5]") {
    // Build a PD string longer than 64 chars (after prepending entity type)
    std::string pd;
    for (int i = 0; i < 20; ++i) {
        if (i > 0) pd += ',';
        pd += "1.23456789";
    }
    pd += ';';
    int seq = 1;
    auto r = split_pd_lines(pd, 110, 1, seq);
    CHECK(r.line_count > 1);
    CHECK(seq == r.line_count + 1);
    // All PD lines should have 'P' at col 73
    for (int i = 0; i < r.line_count; ++i) {
        CHECK(r.lines[i * 81 + 72] == 'P');
    }
}
