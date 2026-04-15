// Tests for §2.2.3 — Rules for Forming and Interpreting Free Formatted Data.
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "parser/param_tokenizer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;

// ─────────────────────────────────────────────────────────────────
// §2.2.3: "The parameter delimiter separates parameters within
//   a record ... The record delimiter terminates a record."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.3 — comma separates parameters", "[parser][spec-2.2.3]") {
    // §2.2.3: "The parameter delimiter separates parameters within a record"
    ParamTokenizer tok("1,2,3;", ',', ';');
    CHECK(tok.next_integer().value() == 1);
    CHECK(tok.next_integer().value() == 2);
    CHECK(tok.next_integer().value() == 3);
    CHECK(tok.at_record_end());
}

TEST_CASE("§2.2.3 — semicolon ends record", "[parser][spec-2.2.3]") {
    // §2.2.3: "The record delimiter terminates a record"
    ParamTokenizer tok("1,2,3;4,5;", ',', ';');
    CHECK(tok.next_integer().value() == 1);
    CHECK(tok.next_integer().value() == 2);
    CHECK(tok.next_integer().value() == 3);
    CHECK(tok.at_record_end());
}

// ─────────────────────────────────────────────────────────────────
// §2.2.3: "An empty field indicates that the value for that
//   parameter is to be set to the default value"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.3 — consecutive delimiters mean defaulted field", "[parser][spec-2.2.3]") {
    // §2.2.3: "An empty field indicates that the value for that
    //   parameter is to be set to the default value"
    ParamTokenizer tok("1,,3;", ',', ';');
    CHECK(tok.next_integer().value() == 1);
    auto field2 = tok.next_field();
    REQUIRE(field2.has_value());
    CHECK(std::holds_alternative<DefaultedField>(field2.value()));
    CHECK(tok.next_integer().value() == 3);
}

TEST_CASE("§2.2.3 — delimiter then record delimiter = defaulted", "[parser][spec-2.2.3]") {
    // §2.2.3: "An empty field indicates that the value for that
    //   parameter is to be set to the default value"
    ParamTokenizer tok("1,;", ',', ';');
    CHECK(tok.next_integer().value() == 1);
    auto field2 = tok.next_field();
    REQUIRE(field2.has_value());
    CHECK(std::holds_alternative<DefaultedField>(field2.value()));
    CHECK(tok.at_record_end());
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2: "Blanks are values only within string fields. For all
//   other data types, an entirely blank (i.e., empty) field
//   indicates a 'defaulted' field."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.3 — delimiters with only blanks between = defaulted", "[parser][spec-2.2.3]") {
    // §2.2.2: "an entirely blank (i.e., empty) field indicates
    //   a 'defaulted' field"
    ParamTokenizer tok("1, ,3;", ',', ';');
    CHECK(tok.next_integer().value() == 1);
    auto field2 = tok.next_field();
    REQUIRE(field2.has_value());
    CHECK(std::holds_alternative<DefaultedField>(field2.value()));
    CHECK(tok.next_integer().value() == 3);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.3: "If the record delimiter is encountered before all
//   required-default parameters are specified, the remaining
//   required-default parameters take their default values."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.3 — early record delimiter assigns defaults to remaining fields",
          "[parser][spec-2.2.3]") {
    // §2.2.3: "If the record delimiter is encountered before all
    //   required-default parameters are specified, the remaining
    //   required-default parameters take their default values."
    ParamTokenizer tok("110,1.0,2.0,3.0;", ',', ';');
    CHECK(tok.next_integer().value() == 110);  // entity type
    CHECK_THAT(tok.next_real().value(), WithinRel(1.0));
    CHECK_THAT(tok.next_real().value(), WithinRel(2.0));
    CHECK_THAT(tok.next_real().value(), WithinRel(3.0));
    CHECK(tok.at_record_end());
    CHECK(tok.next_real_or(0.0).value() == 0.0);
    CHECK(tok.next_real_or(0.0).value() == 0.0);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.5.2: "PD records may be terminated with the record
//   delimiter character prior to the two groups of additional
//   parameters"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.3 — PD record terminated before additional pointer groups",
          "[parser][spec-2.2.3]") {
    // §2.2.4.5.2: "PD records may be terminated with the record delimiter
    //   character prior to the two groups of additional parameters"
    ParamTokenizer tok("110,0.,0.,0.,1.,1.,1.;", ',', ';');
    tok.next_integer();
    for (int i = 0; i < 6; ++i) tok.next_real();
    CHECK(tok.at_record_end());
    CHECK(tok.next_integer_or(0).value() == 0);  // NA
    CHECK(tok.next_integer_or(0).value() == 0);  // NP
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.3: "parameter delimiters, record delimiters ... are
//   counted and included as string characters"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.3 — delimiters inside Hollerith are text", "[parser][spec-2.2.3]") {
    // §2.2.2.3: "parameter delimiters, record delimiters ... are
    //   counted and included as string characters"
    ParamTokenizer tok("5Hhe,lo,2;", ',', ';');
    auto s = tok.next_string();
    REQUIRE(s.has_value());
    CHECK(s.value() == "he,lo");
    CHECK(tok.next_integer().value() == 2);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.3.1: "The parameter delimiter and record delimiter shall
//   each be a single character selected by the preprocessor"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.3 — custom parameter delimiter '|'", "[parser][spec-2.2.3]") {
    // §2.2.3.1: "The parameter delimiter and record delimiter shall each
    //   be a single character selected by the preprocessor"
    ParamTokenizer tok("1|2|3;", '|', ';');
    CHECK(tok.next_integer().value() == 1);
    CHECK(tok.next_integer().value() == 2);
    CHECK(tok.next_integer().value() == 3);
}

TEST_CASE("§2.2.3 — custom record delimiter '#'", "[parser][spec-2.2.3]") {
    // §2.2.3.1: "The parameter delimiter and record delimiter shall each
    //   be a single character selected by the preprocessor"
    ParamTokenizer tok("1,2,3#", ',', '#');
    CHECK(tok.next_integer().value() == 1);
    CHECK(tok.next_integer().value() == 2);
    CHECK(tok.next_integer().value() == 3);
    CHECK(tok.at_record_end());
}
