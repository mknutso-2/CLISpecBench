// Tests for §4.42 — Torus Entity (Type 160).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/torus_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.42 — parse torus", "[entity][spec-4.42]") {
    // §4.42: "Parameters: R1, R2, X1, Y1, Z1, I1, J1, K1"
    ParamTokenizer tok("10.0,2.0,0.0,0.0,0.0,0.0,0.0,1.0;", ',', ';');
    auto r = parse_torus_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().r1 == 10.0);
    CHECK(r.value().r2 == 2.0);
    CHECK(r.value().center.x == 0.0);
    CHECK(r.value().axis.z == 1.0);
}

TEST_CASE("§4.42 — torus defaults", "[entity][spec-4.42]") {
    // §4.42: "Torus center coordinates (default (0.0,0.0,0.0))"
    //        "Unit vector in axis direction (default (0.0,0.0,1.0))"
    ParamTokenizer tok("8.0,1.5,,,,,,;", ',', ';');
    auto r = parse_torus_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().center.x == 0.0);
    CHECK(r.value().center.y == 0.0);
    CHECK(r.value().center.z == 0.0);
    CHECK(r.value().axis.x == 0.0);
    CHECK(r.value().axis.y == 0.0);
    CHECK(r.value().axis.z == 1.0);
}
