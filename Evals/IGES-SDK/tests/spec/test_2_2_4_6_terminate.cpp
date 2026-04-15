// Tests for §2.2.4.6 — Terminate Section.
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "parser/lexer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §2.2.4.6: "There is only one line in the Terminate Section"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.6 — T in column 73 marks terminate section", "[lexer][spec-2.2.4.6]") {
    // §2.2.4.6: "There is only one line in the Terminate Section ...
    //   identified with the letter code 'T' in column 73"
    std::string line = "S      7G      3D     14P      9";
    line.resize(72, ' ');
    line += "T      1";
    auto r = Lexer::parse_line(line, 1);
    REQUIRE(r.has_value());
    CHECK(r.value().kind == SectionKind::Terminate);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.6: "Columns 74 through 80 contain the sequence number
//   with a value of one (1)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.6 — terminate sequence number must be 1", "[lexer][spec-2.2.4.6]") {
    // §2.2.4.6: "Columns 74 through 80 contain the sequence number
    //   with a value of one (1)"
    std::string line = "S      7G      3D     14P      9";
    line.resize(72, ' ');
    line += "T      1";
    auto r = Lexer::parse_line(line, 1);
    REQUIRE(r.has_value());
    CHECK(r.value().sequence_number == 1);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.6: "The data in the Terminate Section comprises the
//   section identification letter and the last sequence number for
//   each section ... in four eight-character fields"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.6 — terminate line data contains section counts", "[lexer][spec-2.2.4.6]") {
    // §2.2.4.6: "Field 1 (cols 1-8): S section count ...
    //   Field 2 (cols 9-16): G section count ...
    //   Field 3 (cols 17-24): D section count ...
    //   Field 4 (cols 25-32): P section count"
    std::string data = "S      7G      3D     14P      9";
    data.resize(72, ' ');
    data += "T      1";
    auto r = Lexer::parse_line(data, 1);
    REQUIRE(r.has_value());
    auto& d = r.value().data;
    // §2.2.4.6: Field 1 (cols 1-8): "S      7"
    CHECK(d.substr(0, 8) == "S      7");
    // §2.2.4.6: Field 2 (cols 9-16): "G      3"
    CHECK(d.substr(8, 8) == "G      3");
    // §2.2.4.6: Field 3 (cols 17-24): "D     14"
    CHECK(d.substr(16, 8) == "D     14");
    // §2.2.4.6: Field 4 (cols 25-32): "P      9"
    CHECK(d.substr(24, 8) == "P      9");
}
