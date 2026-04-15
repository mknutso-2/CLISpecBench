// Tests for §4.49 — Manifold Solid B-Rep Object Entity (Type 186).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/msbo_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.49 — parse MSBO with no voids", "[entity][spec-4.49]") {
    // §4.49: "SHELL: Pointer to the DE of the shell"
    //        "SOF: Orientation flag of shell"
    //        "N: Number of void shells, or zero"
    ParamTokenizer tok("3,1,0;", ',', ';');
    auto r = parse_msbo_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().shell.value == 3);
    CHECK(r.value().sof == true);
    CHECK(r.value().n == 0);
    CHECK(r.value().voids.empty());
}

TEST_CASE("§4.49 — parse MSBO with 1 void", "[entity][spec-4.49]") {
    // §4.49: "VOID(i): Pointer to void shell"
    //        "VOF(i): Orientation flag of void shell"
    ParamTokenizer tok("3,1,1,5,0;", ',', ';');
    auto r = parse_msbo_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 1);
    REQUIRE(r.value().voids.size() == 1);
    CHECK(r.value().voids[0].shell.value == 5);
    CHECK(r.value().voids[0].orientation == false);
}
