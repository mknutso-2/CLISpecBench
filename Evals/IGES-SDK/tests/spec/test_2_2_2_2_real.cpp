// Tests for §2.2.2.2 — Real (floating point) data type.
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "parser/param_tokenizer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;

// ─────────────────────────────────────────────────────────────────
// §2.2.2.2: "The implicit default for a real field is zero."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.2 — implicit default is zero", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2: "The implicit default for a real field is zero."
    auto r = parse_real("");
    CHECK(!r.has_value());
    ParamTokenizer tok(",;", ',', ';');
    auto r2 = tok.next_real_or(0.0);
    REQUIRE(r2.has_value());
    CHECK(r2.value() == 0.0);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.2: "A basic real value contains (in this order) an
//   optional sign, an integer part, a decimal point, a fractional
//   part and an exponent. Both the integer part and the fractional
//   part are sequences of the digits 0-9; either may be omitted,
//   but not both. Either the decimal point or the exponent may be
//   omitted, but not both."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.2 — no integer part (.5)", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2: "either [integer or fractional part] may be omitted, but not both"
    auto r = parse_real(".5");
    REQUIRE(r.has_value());
    CHECK_THAT(r.value(), WithinRel(0.5));
}

TEST_CASE("§2.2.2.2 — no fractional part (5.)", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2: "either [integer or fractional part] may be omitted, but not both"
    auto r = parse_real("5.");
    REQUIRE(r.has_value());
    CHECK_THAT(r.value(), WithinRel(5.0));
}

TEST_CASE("§2.2.2.2 — no decimal point, has exponent (1E3)", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2: "Either the decimal point or the exponent may be omitted, but not both."
    auto r = parse_real("1E3");
    REQUIRE(r.has_value());
    CHECK_THAT(r.value(), WithinRel(1000.0));
}

TEST_CASE("§2.2.2.2 — decimal + fractional, no exponent", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2: "Either the decimal point or the exponent may be omitted, but not both."
    auto r = parse_real("1.5");
    REQUIRE(r.has_value());
    CHECK_THAT(r.value(), WithinRel(1.5));
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.2: "An exponent is either of the letters 'E' or 'D'
//   followed by an optionally signed integer representing the power
//   of ten ... 'E' specifies single-precision ... and 'D' specifies
//   double-precision"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.2 — E exponent", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2: "'E' specifies single-precision"
    auto r = parse_real("1.36E1");
    REQUIRE(r.has_value());
    CHECK_THAT(r.value(), WithinRel(13.6));
}

TEST_CASE("§2.2.2.2 — D exponent (double precision)", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2: "'D' specifies double-precision"
    auto r = parse_real("145.98763D4");
    REQUIRE(r.has_value());
    CHECK_THAT(r.value(), WithinRel(1459876.3));
}

TEST_CASE("§2.2.2.2 — negative E exponent", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2: "An exponent is ... followed by an optionally signed integer
    //   representing the power of ten"
    auto r = parse_real("-1.3E-02");
    REQUIRE(r.has_value());
    CHECK_THAT(r.value(), WithinRel(-0.013));
}

TEST_CASE("§2.2.2.2 — positive E exponent with sign", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2: "followed by an optionally signed integer"
    auto r = parse_real("1.E+4");
    REQUIRE(r.has_value());
    CHECK_THAT(r.value(), WithinRel(10000.0));
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.2: "Neither leading zeros in the integer part nor trailing
//   zeros in the fractional part shall be interpreted as altering
//   accuracy or implying tolerances of real values."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.2 — leading/trailing zeros do not alter value", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2: "Neither leading zeros ... nor trailing zeros ... shall be
    //   interpreted as altering accuracy"
    auto a = parse_real("007.100");
    auto b = parse_real("7.1");
    REQUIRE(a.has_value());
    REQUIRE(b.has_value());
    CHECK(a.value() == b.value());
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.2: "The following are examples of valid real values:
//   256.091  0.  -0.58  +4.21  1.36E1  -1.3E-02  0.1E-3  1.E+4
//   145.98763D4  -2145.980001D-5  0.123456789D+09  -.43E2"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.2 — spec example: 256.091", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2 examples: "256.091"
    CHECK_THAT(parse_real("256.091").value(), WithinRel(256.091));
}

TEST_CASE("§2.2.2.2 — spec example: 0.", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2 examples: "0."
    CHECK_THAT(parse_real("0.").value(), WithinRel(0.0));
}

TEST_CASE("§2.2.2.2 — spec example: -0.58", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2 examples: "-0.58"
    CHECK_THAT(parse_real("-0.58").value(), WithinRel(-0.58));
}

TEST_CASE("§2.2.2.2 — spec example: +4.21", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2 examples: "+4.21"
    CHECK_THAT(parse_real("+4.21").value(), WithinRel(4.21));
}

TEST_CASE("§2.2.2.2 — spec example: 0.1E-3", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2 examples: "0.1E-3"
    CHECK_THAT(parse_real("0.1E-3").value(), WithinRel(0.0001));
}

TEST_CASE("§2.2.2.2 — spec example: -2145.980001D-5", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2 examples: "-2145.980001D-5"
    CHECK_THAT(parse_real("-2145.980001D-5").value(), WithinRel(-0.02145980001));
}

TEST_CASE("§2.2.2.2 — spec example: 0.123456789D+09", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2 examples: "0.123456789D+09"
    CHECK_THAT(parse_real("0.123456789D+09").value(), WithinRel(123456789.0));
}

TEST_CASE("§2.2.2.2 — spec example: -.43E2", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2 examples: "-.43E2"
    CHECK_THAT(parse_real("-.43E2").value(), WithinRel(-43.0));
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2: "A numeric data type may be either signed or unsigned.
//   If signed, the leading plus or minus determines the sense of
//   the number; if unsigned, the sense is non-negative."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.2 — negative zero", "[parser][spec-2.2.2.2]") {
    // §2.2.2: "If signed, the leading plus or minus determines the sense"
    // Negative zero should compare equal to positive zero.
    auto r = parse_real("-0.");
    REQUIRE(r.has_value());
    CHECK(r.value() == 0.0);
}

TEST_CASE("§2.2.2.2 — unsigned exponent is non-negative", "[parser][spec-2.2.2.2]") {
    // §2.2.2.2: "If unsigned, the sense of an exponent is non-negative."
    auto r = parse_real("1.0E3");
    REQUIRE(r.has_value());
    CHECK_THAT(r.value(), WithinRel(1000.0));
}
