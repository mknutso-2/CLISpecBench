// Tests for §4.33 — Bounded Surface Entity (Type 143).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/bounded_surface_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.33: "Parameters: TYPE, SPTR, N, BDPT(1)..BDPT(N)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.33 — parse bounded surface with 1 boundary", "[entity][spec-4.33]") {
    // §4.33: "Parameters: TYPE, SPTR, N, BDPT(1)..BDPT(N)"
    //   TYPE=0 (model space only), SPTR=1, N=1, BDPT(1)=3
    ParamTokenizer tok("0,1,1,3;", ',', ';');
    auto r = parse_bounded_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().type == 0);
    CHECK(r.value().sptr.value == 1);
    CHECK(r.value().n == 1);
    REQUIRE(r.value().bdpt.size() == 1);
    CHECK(r.value().bdpt[0].value == 3);
}

// ─────────────────────────────────────────────────────────────────
// §4.33: "TYPE=0: boundary entities shall reference only model
//   space curves"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.33 — TYPE=0 model space boundaries", "[entity][spec-4.33]") {
    // §4.33: "0 = The boundary entities shall reference only model
    //   space curves"
    ParamTokenizer tok("0,5,2,7,9;", ',', ';');
    auto r = parse_bounded_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().type == 0);
    CHECK(r.value().bdpt.size() == 2);
}

// ─────────────────────────────────────────────────────────────────
// §4.33: "TYPE=1: boundary entities shall reference both model
//   space curves and the associated parameter space curve
//   collections"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.33 — TYPE=1 model + parameter space boundaries", "[entity][spec-4.33]") {
    // §4.33: "1 = The boundary entities shall reference both model
    //   space curves and the associated parameter space curve collections"
    ParamTokenizer tok("1,5,1,7;", ',', ';');
    auto r = parse_bounded_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().type == 1);
}

// ─────────────────────────────────────────────────────────────────
// §4.33: "N: The number of boundary entities"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.33 — bounded surface with 3 boundaries", "[entity][spec-4.33]") {
    // §4.33: "N: The number of boundary entities"
    ParamTokenizer tok("0,1,3,5,7,9;", ',', ';');
    auto r = parse_bounded_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 3);
    REQUIRE(r.value().bdpt.size() == 3);
    CHECK(r.value().bdpt[0].value == 5);
    CHECK(r.value().bdpt[1].value == 7);
    CHECK(r.value().bdpt[2].value == 9);
}
