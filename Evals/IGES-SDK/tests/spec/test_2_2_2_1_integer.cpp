// Tests for §2.2.2.1 — Integer data type.
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §2.2.2.1: "An integer (i.e., a fixed point value) always
//   represents an integer value exactly."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.1 — integer represents value exactly", "[parser][spec-2.2.2.1]") {
    // §2.2.2.1: "An integer ... always represents an integer value exactly."
    auto r = parse_integer("150");
    REQUIRE(r.has_value());
    CHECK(r.value() == 150);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.1: "It may have a positive, negative, or zero value."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.1 — positive integer", "[parser][spec-2.2.2.1]") {
    // §2.2.2.1: "It may have a positive ... value."
    auto r = parse_integer("+3451");
    REQUIRE(r.has_value());
    CHECK(r.value() == 3451);
}

TEST_CASE("§2.2.2.1 — negative integer", "[parser][spec-2.2.2.1]") {
    // §2.2.2.1: "It may have a ... negative ... value."
    auto r = parse_integer("-2147483647");
    REQUIRE(r.has_value());
    CHECK(r.value() == -2147483647);
}

TEST_CASE("§2.2.2.1 — zero integer", "[parser][spec-2.2.2.1]") {
    // §2.2.2.1: "It may have a ... zero value."
    auto r = parse_integer("0");
    REQUIRE(r.has_value());
    CHECK(r.value() == 0);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.1: "The implicit default for an integer field is zero."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.1 — implicit default is zero", "[parser][spec-2.2.2.1]") {
    // §2.2.2.1: "The implicit default for an integer field is zero."
    ParamTokenizer tok(",;", ',', ';');
    auto r = tok.next_integer_or(0);
    REQUIRE(r.has_value());
    CHECK(r.value() == 0);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.1: "An integer has an optional sign followed by a
//   non-empty string of digits representing a decimal number."
// Examples from spec: "1 150 2147483647 +3451 0 -1 -2147483647"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.1 — spec example values", "[parser][spec-2.2.2.1]") {
    // §2.2.2.1: "The following are examples of valid integers
    //   (assuming the value of Global Parameter 7 is 32):
    //   1 150 2147483647 +3451 0 -1 0 -2147483647"
    CHECK(parse_integer("1").value() == 1);
    CHECK(parse_integer("150").value() == 150);
    CHECK(parse_integer("2147483647").value() == 2147483647);
    CHECK(parse_integer("+3451").value() == 3451);
    CHECK(parse_integer("0").value() == 0);
    CHECK(parse_integer("-1").value() == -1);
    CHECK(parse_integer("-2147483647").value() == -2147483647);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2: "Postprocessors shall ignore leading blanks in numeric
//   fields."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.1 — leading blanks ignored", "[parser][spec-2.2.2.1][spec-2.2.2]") {
    // §2.2.2: "Postprocessors shall ignore leading blanks in numeric fields."
    auto r = parse_integer("   42");
    REQUIRE(r.has_value());
    CHECK(r.value() == 42);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2: "Blanks are values only within string fields. For all
//   other data types, an entirely blank (i.e., empty) field
//   indicates a 'defaulted' field."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.1 — all-blank field is defaulted", "[parser][spec-2.2.2.1][spec-2.2.2]") {
    // §2.2.2: "For all other data types, an entirely blank (i.e., empty)
    //   field indicates a 'defaulted' field."
    auto r = parse_integer("        ");
    CHECK(!r.has_value());
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2: "A numeric data type may be either signed or unsigned.
//   If signed, the leading plus or minus determines the sense of
//   the number; if unsigned, the sense is non-negative."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.1 — unsigned integer is non-negative", "[parser][spec-2.2.2.1]") {
    // §2.2.2: "if unsigned, the sense is non-negative."
    auto r = parse_integer("42");
    REQUIRE(r.has_value());
    CHECK(r.value() == 42);
}

TEST_CASE("§2.2.2.1 — explicit positive sign", "[parser][spec-2.2.2.1]") {
    // §2.2.2: "If signed, the leading plus or minus determines the sense"
    // §2.2.2.1: "An integer has an optional sign followed by a non-empty
    //   string of digits"
    auto r = parse_integer("+0");
    REQUIRE(r.has_value());
    CHECK(r.value() == 0);
}
