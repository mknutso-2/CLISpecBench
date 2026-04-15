// Tests for §2.2.4.2 — Start Section.
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "parser/lexer.hpp"

#include <sstream>

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §2.2.4.2: "Start Section lines are identified with the letter
//   code 'S' in column 73"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.2 — S in column 73 marks start section", "[lexer][spec-2.2.4.2]") {
    // §2.2.4.2: "Start Section lines are identified with the letter
    //   code 'S' in column 73"
    std::string line(72, ' ');
    line += "S      1";
    auto r = Lexer::parse_line(line, 1);
    REQUIRE(r.has_value());
    CHECK(r.value().kind == SectionKind::Start);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.2: "sequenced in columns 74–80"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.2 — sequence number parsed from columns 74-80", "[lexer][spec-2.2.4.2]") {
    // §2.2.4.2: "sequenced in columns 74–80"
    std::string line(72, ' ');
    line += "S      3";
    auto r = Lexer::parse_line(line, 3);
    REQUIRE(r.has_value());
    CHECK(r.value().sequence_number == 3);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.2: "one data field in columns 1–72"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.2 — data from columns 1-72", "[lexer][spec-2.2.4.2]") {
    // §2.2.4.2: "one data field in columns 1–72"
    std::string data = "This is a test prologue.";
    data.resize(72, ' ');
    data += "S      1";
    auto r = Lexer::parse_line(data, 1);
    REQUIRE(r.has_value());
    CHECK(r.value().data.size() == 72);
    CHECK(r.value().data.substr(0, 24) == "This is a test prologue.");
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.2: "shall not contain any ASCII control characters
//   (i.e., hexadecimal 00 through 1F and hexadecimal 7F)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.2 — control chars in data rejected", "[lexer][spec-2.2.4.2]") {
    // §2.2.4.2: "shall not contain any ASCII control characters
    //   (i.e., hexadecimal 00 through 1F)"
    std::string data(72, ' ');
    data[10] = '\x01';  // control character
    data += "S      1";
    auto r = Lexer::parse_line(data, 1);
    CHECK(!r.has_value());
}

TEST_CASE("§2.2.4.2 — DEL (0x7F) in data rejected", "[lexer][spec-2.2.4.2]") {
    // §2.2.4.2: "shall not contain any ASCII control characters
    //   (i.e., ... hexadecimal 7F)"
    std::string data(72, ' ');
    data[10] = '\x7F';
    data += "S      1";
    auto r = Lexer::parse_line(data, 1);
    CHECK(!r.has_value());
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.2: "At least one Start Section line shall appear in every
//   file"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.2 — file with no start section lines is invalid", "[lexer][spec-2.2.4.2]") {
    // §2.2.4.2: "At least one Start Section line shall appear in every file"
    std::string global_line(72, ' ');
    global_line += "G      1";
    std::string term_line = "S      0G      0D      0P      0";
    term_line.resize(72, ' ');
    term_line += "T      1";

    std::istringstream input(global_line + "\n" + term_line + "\n");
    auto r = Lexer::read_all(input);
    CHECK(!r.has_value());
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.2: "even if it is blank except for the sequence field"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.2 — blank start line is valid", "[lexer][spec-2.2.4.2]") {
    // §2.2.4.2: "At least one Start Section line shall appear ...
    //   even if it is blank except for the sequence field"
    std::string line(72, ' ');
    line += "S      1";
    auto r = Lexer::parse_line(line, 1);
    REQUIRE(r.has_value());
    CHECK(r.value().kind == SectionKind::Start);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4: Section code validation — "S, G, D, P, T" are the valid
//   section identification letters (col 73)
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.2 — 'S' is a valid section code", "[lexer][spec-2.2.4.2]") {
    // §2.2.4: "S" identifies the Start Section
    CHECK(Lexer::is_section_code('S'));
}

TEST_CASE("§2.2.4.2 — 'G' is a valid section code", "[lexer][spec-2.2.4.2]") {
    // §2.2.4: "G" identifies the Global Section
    CHECK(Lexer::is_section_code('G'));
}

TEST_CASE("§2.2.4.2 — 'D' is a valid section code", "[lexer][spec-2.2.4.2]") {
    // §2.2.4: "D" identifies the Directory Entry Section
    CHECK(Lexer::is_section_code('D'));
}

TEST_CASE("§2.2.4.2 — 'P' is a valid section code", "[lexer][spec-2.2.4.2]") {
    // §2.2.4: "P" identifies the Parameter Data Section
    CHECK(Lexer::is_section_code('P'));
}

TEST_CASE("§2.2.4.2 — 'T' is a valid section code", "[lexer][spec-2.2.4.2]") {
    // §2.2.4: "T" identifies the Terminate Section
    CHECK(Lexer::is_section_code('T'));
}

TEST_CASE("§2.2.4.2 — 'C' (compressed flag) is a valid section code", "[lexer][spec-2.2.4.2]") {
    // §2.2.4.1: "C" identifies the Flag Section (Binary/Compressed)
    CHECK(Lexer::is_section_code('C'));
}

TEST_CASE("§2.2.4.2 — 'X' is not a valid section code", "[lexer][spec-2.2.4.2]") {
    // §2.2.4: Only S, G, D, P, T, C are valid section identification letters
    CHECK(!Lexer::is_section_code('X'));
}

TEST_CASE("§2.2.4.2 — lowercase 's' is not a valid section code", "[lexer][spec-2.2.4.2]") {
    // §2.2.4: Section codes are uppercase only
    CHECK(!Lexer::is_section_code('s'));
}
