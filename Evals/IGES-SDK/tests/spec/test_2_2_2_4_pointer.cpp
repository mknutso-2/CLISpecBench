// Tests for §2.2.2.4 — Pointer data type.
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §2.2.2.4: "A pointer value shall be an integer with a value in
//   the range -9999999 through 9999999"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.4 — valid positive pointer", "[parser][spec-2.2.2.4]") {
    // §2.2.2.4: "A pointer value shall be an integer with a value in
    //   the range -9999999 through 9999999"
    auto r = parse_integer("1");
    REQUIRE(r.has_value());
    CHECK(r.value() == 1);
}

TEST_CASE("§2.2.2.4 — valid negative pointer", "[parser][spec-2.2.2.4]") {
    // §2.2.2.4: "A pointer value shall be an integer with a value in
    //   the range -9999999 through 9999999"
    auto r = parse_integer("-9999999");
    REQUIRE(r.has_value());
    CHECK(r.value() == -9999999);
}

TEST_CASE("§2.2.2.4 — max positive pointer", "[parser][spec-2.2.2.4]") {
    // §2.2.2.4: "A pointer value shall be an integer with a value in
    //   the range -9999999 through 9999999"
    auto r = parse_integer("9999999");
    REQUIRE(r.has_value());
    CHECK(r.value() == 9999999);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.4: "The implicit default for a pointer field is zero
//   (i.e., a null pointer)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.4 — implicit default is zero", "[parser][spec-2.2.2.4]") {
    // §2.2.2.4: "The implicit default for a pointer field is zero
    //   (i.e., a null pointer)"
    ParamTokenizer tok(",;", ',', ';');
    auto r = tok.next_pointer();
    REQUIRE(r.has_value());
    CHECK(r.value().is_null());
    CHECK(r.value().value == 0);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.4: "Leading-zero or leading-space fill may be used in
//   fixed-length fields"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.4 — leading-zero fill", "[parser][spec-2.2.2.4]") {
    // §2.2.2.4: "Leading-zero or leading-space fill may be used"
    auto r = parse_integer("0000001");
    REQUIRE(r.has_value());
    CHECK(r.value() == 1);
}

TEST_CASE("§2.2.2.4 — leading-space fill", "[parser][spec-2.2.2.4]") {
    // §2.2.2.4: "Leading-zero or leading-space fill may be used"
    auto r = parse_integer("      1");
    REQUIRE(r.has_value());
    CHECK(r.value() == 1);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.4: "Negated pointer values occur in those fields which
//   define a different meaning for a zero or positive value"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.4 — negated pointer in color field", "[parser][spec-2.2.2.4]") {
    // §2.2.2.4: "Negated pointer values occur in those fields which
    //   define a different meaning for a zero or positive value"
    // e.g., color field = -7 means pointer to DE 7 (a Color Definition Entity)
    auto r = parse_integer("-7");
    REQUIRE(r.has_value());
    CHECK(r.value() == -7);
    // In ColorVariant interpretation:
    ColorVariant cv;
    cv.raw = -7;
    CHECK(cv.is_pointer());
    CHECK(cv.pointer().value == 7);
}
