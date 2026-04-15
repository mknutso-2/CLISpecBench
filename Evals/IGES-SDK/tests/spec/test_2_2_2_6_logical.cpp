// Tests for §2.2.2.6 — Logical data type.
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §2.2.2.6: "A logical value may have the value TRUE or FALSE.
//   An integer 0 denotes FALSE and a nonzero integer denotes TRUE."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.6 — 0 is FALSE", "[parser][spec-2.2.2.6]") {
    // §2.2.2.6: "An integer 0 denotes FALSE"
    ParamTokenizer tok("0;", ',', ';');
    auto r = tok.next_logical();
    REQUIRE(r.has_value());
    CHECK(r.value() == false);
}

TEST_CASE("§2.2.2.6 — 1 is TRUE", "[parser][spec-2.2.2.6]") {
    // §2.2.2.6: "a nonzero integer denotes TRUE"
    ParamTokenizer tok("1;", ',', ';');
    auto r = tok.next_logical();
    REQUIRE(r.has_value());
    CHECK(r.value() == true);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.2.6: "The implicit default for a logical field is FALSE."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.2.6 — implicit default is FALSE", "[parser][spec-2.2.2.6]") {
    // §2.2.2.6: "The implicit default for a logical field is FALSE."
    ParamTokenizer tok(",;", ',', ';');  // empty field
    auto r = tok.next_logical_or(false);
    REQUIRE(r.has_value());
    CHECK(r.value() == false);
}
