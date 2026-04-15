// Tests for ParamWriter — builds PD strings from typed fields.
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "writer/param_writer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §2.2.3: "Free-format ... parameter delimiter character separates
//   consecutive parameters"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("ParamWriter — single integer", "[writer][spec-2.2.3]") {
    ParamWriter pw;
    pw.write_integer(42);
    pw.end_record();
    CHECK(pw.str() == "42;");
}

TEST_CASE("ParamWriter — multiple fields comma-separated", "[writer][spec-2.2.3]") {
    // §2.2.3: Fields separated by parameter delimiter
    ParamWriter pw;
    pw.write_integer(110);
    pw.write_real(1.0);
    pw.write_real(2.0);
    pw.end_record();
    auto s = pw.str();
    // Should have commas between fields and semicolon at end
    CHECK(s.front() != ',');
    CHECK(s.back() == ';');
    CHECK(s.find(',') != std::string::npos);
}

TEST_CASE("ParamWriter — pointer field", "[writer][spec-2.2.2.4]") {
    ParamWriter pw;
    pw.write_pointer(DEIndex{5});
    pw.end_record();
    CHECK(pw.str() == "5;");
}

TEST_CASE("ParamWriter — null pointer as 0", "[writer][spec-2.2.2.4]") {
    ParamWriter pw;
    pw.write_pointer(DEIndex{0});
    pw.end_record();
    CHECK(pw.str() == "0;");
}

TEST_CASE("ParamWriter — string field as Hollerith", "[writer][spec-2.2.2.3]") {
    ParamWriter pw;
    pw.write_string("hello");
    pw.end_record();
    CHECK(pw.str() == "5Hhello;");
}

TEST_CASE("ParamWriter — logical field", "[writer][spec-2.2.2.6]") {
    ParamWriter pw;
    pw.write_logical(true);
    pw.write_logical(false);
    pw.end_record();
    CHECK(pw.str() == "1,0;");
}

TEST_CASE("ParamWriter — line entity round-trip format", "[writer]") {
    // Build what parse_line_entity expects
    ParamWriter pw;
    pw.write_real(1.0);
    pw.write_real(2.0);
    pw.write_real(3.0);
    pw.write_real(4.0);
    pw.write_real(5.0);
    pw.write_real(6.0);
    pw.end_record();
    auto s = pw.str();
    // Should be parseable back
    CHECK(s.back() == ';');
    // Should have 5 commas (6 fields)
    int commas = 0;
    for (char c : s) if (c == ',') ++commas;
    CHECK(commas == 5);
}
