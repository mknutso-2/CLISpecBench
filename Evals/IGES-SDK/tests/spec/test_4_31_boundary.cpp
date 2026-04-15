// Tests for §4.31 — Boundary Entity (Type 141).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/boundary_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.31: "Parameters: TYPE, PREF, SPTR, N, then per-curve:
//   CRVPT(i), SENSE(i), K(i), PSCPT(i,1)...PSCPT(i,K(i))"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.31 — parse boundary TYPE=0 single curve no param curves", "[entity][spec-4.31]") {
    // §4.31: "TYPE=0: boundary entities shall reference only model
    //   space trimming curves ... K(i) shall be zero"
    ParamTokenizer tok("0,1,5,1,7,1,0;", ',', ';');
    auto r = parse_boundary_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().type == 0);
    CHECK(r.value().pref == 1);
    CHECK(r.value().sptr.value == 5);
    CHECK(r.value().n == 1);
    REQUIRE(r.value().curves.size() == 1);
    CHECK(r.value().curves[0].crvpt.value == 7);
    CHECK(r.value().curves[0].sense == 1);
    CHECK(r.value().curves[0].k == 0);
    CHECK(r.value().curves[0].pscpt.empty());
}

TEST_CASE("§4.31 — parse boundary TYPE=1 with parameter space curves", "[entity][spec-4.31]") {
    // §4.31: "TYPE=1: boundary entities shall reference model space
    //   curves and associated parameter space curve collections"
    ParamTokenizer tok("1,2,5,1,7,1,2,9,11;", ',', ';');
    auto r = parse_boundary_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().type == 1);
    CHECK(r.value().pref == 2);
    REQUIRE(r.value().curves.size() == 1);
    CHECK(r.value().curves[0].crvpt.value == 7);
    CHECK(r.value().curves[0].sense == 1);
    CHECK(r.value().curves[0].k == 2);
    REQUIRE(r.value().curves[0].pscpt.size() == 2);
    CHECK(r.value().curves[0].pscpt[0].value == 9);
    CHECK(r.value().curves[0].pscpt[1].value == 11);
}

TEST_CASE("§4.31 — parse boundary with multiple curves", "[entity][spec-4.31]") {
    // §4.31: "N: Number of curves included in this boundary entity (N > 0)"
    ParamTokenizer tok("0,0,3,2,5,1,0,7,2,0;", ',', ';');
    auto r = parse_boundary_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 2);
    REQUIRE(r.value().curves.size() == 2);
    CHECK(r.value().curves[0].crvpt.value == 5);
    CHECK(r.value().curves[0].sense == 1);
    CHECK(r.value().curves[1].crvpt.value == 7);
    CHECK(r.value().curves[1].sense == 2);
}

TEST_CASE("§4.31 — SENSE flag values", "[entity][spec-4.31]") {
    // §4.31: "SENSE: 1 = direction does not require reversal;
    //   2 = direction needs to be reversed"
    ParamTokenizer tok("0,0,1,1,3,2,0;", ',', ';');
    auto r = parse_boundary_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().curves[0].sense == 2);
}
