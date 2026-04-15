// Tests for §2.2.3.1 — Parameter and Record Delimiter Combinations.
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §2.2.3.1: "Neither the parameter delimiter nor the record
//   delimiter shall be any of the following: ... digits 0 through 9,
//   space, plus, minus, period, D, E, H, or ASCII control chars"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.3.1 — control characters prohibited as delimiters",
          "[parser][spec-2.2.3.1]") {
    // §2.2.3.1: "Neither ... shall be ... ASCII control characters
    //   (hexadecimal 00 through 1F and 7F)"
    CHECK(!is_valid_delimiter('\x00'));
    CHECK(!is_valid_delimiter('\x01'));
    CHECK(!is_valid_delimiter('\x1F'));
    CHECK(!is_valid_delimiter('\x7F'));
}

TEST_CASE("§2.2.3.1 — space prohibited as delimiter", "[parser][spec-2.2.3.1]") {
    // §2.2.3.1: "Neither ... shall be ... a space"
    CHECK(!is_valid_delimiter(' '));
}

TEST_CASE("§2.2.3.1 — digits 0-9 prohibited as delimiters", "[parser][spec-2.2.3.1]") {
    // §2.2.3.1: "Neither ... shall be ... digits 0 through 9"
    for (char c = '0'; c <= '9'; ++c) {
        CHECK(!is_valid_delimiter(c));
    }
}

TEST_CASE("§2.2.3.1 — +, -, . prohibited as delimiters", "[parser][spec-2.2.3.1]") {
    // §2.2.3.1: "Neither ... shall be ... a plus, minus, or period"
    CHECK(!is_valid_delimiter('+'));
    CHECK(!is_valid_delimiter('-'));
    CHECK(!is_valid_delimiter('.'));
}

TEST_CASE("§2.2.3.1 — D, E, H prohibited as delimiters", "[parser][spec-2.2.3.1]") {
    // §2.2.3.1: "Neither ... shall be ... the letters D, E, or H"
    CHECK(!is_valid_delimiter('D'));
    CHECK(!is_valid_delimiter('E'));
    CHECK(!is_valid_delimiter('H'));
}

// ─────────────────────────────────────────────────────────────────
// §2.2.3.1: Valid delimiter characters (not in the prohibited list)
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.3.1 — comma is valid delimiter", "[parser][spec-2.2.3.1]") {
    // §2.2.3.1: comma is the default parameter delimiter
    CHECK(is_valid_delimiter(','));
}

TEST_CASE("§2.2.3.1 — semicolon is valid delimiter", "[parser][spec-2.2.3.1]") {
    // §2.2.3.1: semicolon is the default record delimiter
    CHECK(is_valid_delimiter(';'));
}

TEST_CASE("§2.2.3.1 — pipe is valid delimiter", "[parser][spec-2.2.3.1]") {
    // §2.2.3.1: not in the prohibited list, so valid as a delimiter
    CHECK(is_valid_delimiter('|'));
}

TEST_CASE("§2.2.3.1 — hash is valid delimiter", "[parser][spec-2.2.3.1]") {
    // §2.2.3.1: not in the prohibited list, so valid as a delimiter
    CHECK(is_valid_delimiter('#'));
}

TEST_CASE("§2.2.3.1 — tilde is valid delimiter", "[parser][spec-2.2.3.1]") {
    // §2.2.3.1: not in the prohibited list, so valid as a delimiter
    CHECK(is_valid_delimiter('~'));
}

// ─────────────────────────────────────────────────────────────────
// §2.2.3.1: "Four forms of parameter and record delimiter
//   combination are allowed"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.3.1 — Form 1: default delimiters (comma, semicolon)",
          "[parser][spec-2.2.3.1]") {
    // §2.2.3.1: "Form 1: Both fields are defaulted ... the comma and
    //   semicolon are the delimiters"
    ParamTokenizer tok("1,2;", ',', ';');
    CHECK(tok.next_integer().value() == 1);
    CHECK(tok.next_integer().value() == 2);
    CHECK(tok.at_record_end());
}

TEST_CASE("§2.2.3.1 — Form 2: custom param and record delimiters via 1Hα 1Hβ",
          "[parser][spec-2.2.3.1]") {
    // §2.2.3.1: "Form 2: Both fields contain a 1H Hollerith constant
    //   specifying the delimiter character"
    ParamTokenizer tok("1|2#", '|', '#');
    CHECK(tok.next_integer().value() == 1);
    CHECK(tok.next_integer().value() == 2);
    CHECK(tok.at_record_end());
}

TEST_CASE("§2.2.3.1 — Form 3: custom param delimiter only",
          "[parser][spec-2.2.3.1]") {
    // §2.2.3.1: "Form 3: Parameter 1 contains a 1H Hollerith constant ...
    //   Parameter 2 is defaulted (semicolon)"
    ParamTokenizer tok("1|2;", '|', ';');
    CHECK(tok.next_integer().value() == 1);
    CHECK(tok.next_integer().value() == 2);
    CHECK(tok.at_record_end());
}

TEST_CASE("§2.2.3.1 — Form 4: default param delimiter, custom record",
          "[parser][spec-2.2.3.1]") {
    // §2.2.3.1: "Form 4: Parameter 1 is defaulted (comma) ...
    //   Parameter 2 contains a 1H Hollerith constant"
    ParamTokenizer tok("1,2#", ',', '#');
    CHECK(tok.next_integer().value() == 1);
    CHECK(tok.next_integer().value() == 2);
    CHECK(tok.at_record_end());
}
