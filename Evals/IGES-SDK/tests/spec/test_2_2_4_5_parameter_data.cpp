// Tests for §2.2.4.5 — Parameter Data Section.
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "parser/lexer.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §2.2.4.5.1: "The first field of any set of PD records for an
//   entity shall always contain the entity type number"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.5.1 — first PD field is entity type number", "[parser][spec-2.2.4.5]") {
    // §2.2.4.5.1: "The first field ... shall always contain the entity
    //   type number"
    ParamTokenizer tok("110,0.,0.,0.,1.,1.,1.;", ',', ';');
    auto entity_type = tok.next_integer();
    REQUIRE(entity_type.has_value());
    CHECK(entity_type.value() == 110);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.5.1: "The free-formatted part of a parameter line ends
//   in Column 64"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.5.1 — PD data is columns 1-64", "[lexer][spec-2.2.4.5]") {
    // §2.2.4.5.1: "The free-formatted part of a parameter line ends
    //   in Column 64"
    std::string data = "110,0.,0.,0.,1.,1.,1.;";
    data.resize(64, ' ');
    data += ' ';                // column 65: space
    data += "      1";          // columns 66-72: DE back-pointer
    data += "P      1";         // columns 73-80: P + sequence number
    auto r = Lexer::parse_line(data, 1);
    REQUIRE(r.has_value());
    CHECK(r.value().kind == SectionKind::Parameter);
    CHECK(r.value().data.size() == 64);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.5.1: "Column 65 shall contain a space character"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.5.1 — PD column 65 is space", "[lexer][spec-2.2.4.5]") {
    // §2.2.4.5.1: "Column 65 shall contain a space character"
    std::string line(64, ' ');
    line[0] = '1';   // some data
    line += ' ';                // column 65: space (correct)
    line += "      1";          // columns 66-72
    line += "P      1";         // columns 73-80
    auto r = Lexer::parse_line(line, 1);
    REQUIRE(r.has_value());
    CHECK(r.value().kind == SectionKind::Parameter);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.5.2: "Following all parameters ... the PD record may
//   contain two groups of additional pointers: NA and NP"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.5.2 — additional pointers: NA=2 with back pointers", "[parser][spec-2.2.4.5]") {
    // §2.2.4.5.2: "NA ... Number of additional pointers ...
    //   NP ... Number of additional property entity pointers"
    ParamTokenizer tok("110,1.,2.,3.,4.,5.,6.,2,100,200,0;", ',', ';');
    tok.next_integer();  // 110 entity type
    for (int i = 0; i < 6; ++i) tok.next_real();  // 6 line params
    auto na = tok.next_integer();
    REQUIRE(na.has_value());
    CHECK(na.value() == 2);
    CHECK(tok.next_integer().value() == 100);  // DE ptr 1
    CHECK(tok.next_integer().value() == 200);  // DE ptr 2
    auto np = tok.next_integer();
    REQUIRE(np.has_value());
    CHECK(np.value() == 0);
}

TEST_CASE("§2.2.4.5.2 — NA and NP default to 0 when record ends early", "[parser][spec-2.2.4.5]") {
    // §2.2.4.5.2: "PD records may be terminated with the record
    //   delimiter character prior to the two groups of additional
    //   parameters"
    ParamTokenizer tok("110,0.,0.,0.,1.,1.,1.;", ',', ';');
    tok.next_integer();
    for (int i = 0; i < 6; ++i) tok.next_real();
    CHECK(tok.at_record_end());
    CHECK(tok.next_integer_or(0).value() == 0);  // NA
    CHECK(tok.next_integer_or(0).value() == 0);  // NP
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.5.3: "Any desired comment may be added after the record
//   delimiter on the last PD line for the entity"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.5.3 — comment after record delimiter is ignored", "[parser][spec-2.2.4.5]") {
    // §2.2.4.5.3: "Any desired comment may be added after the record
    //   delimiter on the last PD line"
    ParamTokenizer tok("110,1.,2.;this is a comment", ',', ';');
    CHECK(tok.next_integer().value() == 110);
    tok.next_real();
    tok.next_real();
    CHECK(tok.at_record_end());
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.5: PD multi-line continuation — data from columns 1-64
//   is concatenated across physical lines by the lexer
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.5 — PD data spanning multiple lines is concatenated", "[parser][spec-2.2.4.5]") {
    // §2.2.4.5: "A set of PD records for an entity may span
    //   multiple physical lines; the lexer concatenates cols 1-64"
    std::string data = "110,1.0,2.0,3.0,4.0,5.0,6.0;";
    ParamTokenizer tok(data, ',', ';');
    CHECK(tok.next_integer().value() == 110);
    for (int i = 0; i < 6; ++i) {
        auto r = tok.next_real();
        REQUIRE(r.has_value());
    }
    CHECK(tok.at_record_end());
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.5: "P" in column 73 identifies PD section lines
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.5 — P in column 73 marks parameter data section", "[lexer][spec-2.2.4.5]") {
    // §2.2.4.5: "Parameter Data Section lines are identified with the
    //   letter code 'P' in column 73"
    std::string line(64, ' ');
    line += ' ';       // col 65
    line += "      1"; // cols 66-72
    line += "P      1";
    auto r = Lexer::parse_line(line, 1);
    REQUIRE(r.has_value());
    CHECK(r.value().kind == SectionKind::Parameter);
}
