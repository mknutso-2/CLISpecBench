// Tests for §2.2.2.3 — String (Hollerith) data type.
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §2.2.2.3: "A string constant consists of a character count
//   followed by an 'H' ... followed by the character string itself"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.3 — basic Hollerith parse", "[parser][spec-2.2.2.3]") {
    // §2.2.2.3: "A string constant consists of a character count
    //   followed by an 'H' ... followed by the character string itself"
    auto r = parse_hollerith_string("3H123");
    REQUIRE(r.has_value());
    CHECK(r.value() == "123");
}

TEST_CASE("§2.2.2.3 — Hollerith with spaces", "[parser][spec-2.2.2.3]") {
    // §2.2.2.3: "A string constant consists of a character count
    //   followed by an 'H' ... followed by the character string itself"
    auto r = parse_hollerith_string("12H HELLO THERE");
    REQUIRE(r.has_value());
    CHECK(r.value() == " HELLO THERE");
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.3: "parameter delimiters, record delimiters ... are
//   counted and included as string characters"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.3 — delimiters within string are ordinary", "[parser][spec-2.2.2.3]") {
    // §2.2.2.3: "parameter delimiters, record delimiters ... are
    //   counted and included as string characters"
    auto r = parse_hollerith_string("10HABC ., ; AB");
    REQUIRE(r.has_value());
    CHECK(r.value() == "ABC ., ; A");   // 10 characters
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.3: "The implicit default for a string field ... is the
//   NULL string (zero length)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.3 — implicit default is null/empty", "[parser][spec-2.2.2.3]") {
    // §2.2.2.3: "The implicit default for a string field ... is the
    //   NULL string (zero length)"
    ParamTokenizer tok(",;", ',', ';');
    auto r = tok.next_string_or("");
    REQUIRE(r.has_value());
    CHECK(r.value().empty());
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.3: "The string shall not contain ASCII control characters
//   (hex 00-1F, 7F)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.3 — control character in string rejected", "[parser][spec-2.2.2.3]") {
    // §2.2.2.3: "The string shall not contain ASCII control characters
    //   (hex 00-1F, 7F)"
    std::string bad = "3H" + std::string("A\x01" "B");
    auto r = parse_hollerith_string(bad);
    CHECK(!r.has_value());
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.3: Spec examples — "3H123", "8H0.457E03"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.3 — spec example: 3H123", "[parser][spec-2.2.2.3]") {
    // §2.2.2.3: "The following are examples of valid string constants: 3H123"
    CHECK(parse_hollerith_string("3H123").value() == "123");
}

TEST_CASE("§2.2.2.3 — spec example: 8H0.457E03", "[parser][spec-2.2.2.3]") {
    // §2.2.2.3: "The following are examples of valid string constants: ...
    //   8H0.457E03"
    CHECK(parse_hollerith_string("8H0.457E03").value() == "0.457E03");
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.3: "The character count is a nonzero unsigned integer"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.3 — zero character count is invalid", "[parser][spec-2.2.2.3]") {
    // §2.2.2.3: "The character count is a nonzero unsigned integer"
    auto r = parse_hollerith_string("0H");
    CHECK(!r.has_value());
}

TEST_CASE("§2.2.2.3 — negative character count is invalid", "[parser][spec-2.2.2.3]") {
    // §2.2.2.3: "The character count is a nonzero unsigned integer"
    auto r = parse_hollerith_string("-1H");
    CHECK(!r.has_value());
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2: "A string field may cross physical line boundaries
//   within the file"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.3 — string crossing line boundary", "[parser][spec-2.2.2.3][spec-2.2.2]") {
    // §2.2.2: "A string field may cross physical line boundaries"
    // The tokenizer receives concatenated data from the lexer, so this
    // is transparent.
    auto r = parse_hollerith_string("10HABCDEFGHIJ");
    REQUIRE(r.has_value());
    CHECK(r.value() == "ABCDEFGHIJ");
}

// ─────────────────────────────────────────────────────────────────
// §2.2.1: "a space-filled Hollerith string is NOT a defaulted field"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.3 — blank Hollerith is not defaulted", "[parser][spec-2.2.2.3][spec-2.2.1]") {
    // §2.2.1: "a space-filled Hollerith string is NOT a defaulted field"
    auto r = parse_hollerith_string("4H    ");
    REQUIRE(r.has_value());
    CHECK(r.value() == "    ");
    CHECK(!r.value().empty());  // NOT defaulted
}
