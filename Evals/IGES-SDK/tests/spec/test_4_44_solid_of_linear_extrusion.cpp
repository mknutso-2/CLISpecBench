// Tests for §4.44 — Solid of Linear Extrusion Entity (Type 164).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/solid_of_linear_extrusion_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.44 — parse solid of linear extrusion", "[entity][spec-4.44]") {
    // §4.44: "Parameters: PTR, L, I1, J1, K1"
    ParamTokenizer tok("3,10.0,0.0,0.0,1.0;", ',', ';');
    auto r = parse_solid_of_linear_extrusion_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().ptr.value == 3);
    CHECK(r.value().length == 10.0);
    CHECK(r.value().direction.x == 0.0);
    CHECK(r.value().direction.y == 0.0);
    CHECK(r.value().direction.z == 1.0);
}

TEST_CASE("§4.44 — extrusion direction defaults", "[entity][spec-4.44]") {
    // §4.44: "Unit vector specifying direction of extrusion
    //   (default (0.0,0.0,1.0))"
    ParamTokenizer tok("5,20.0,,,;", ',', ';');
    auto r = parse_solid_of_linear_extrusion_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().direction.x == 0.0);
    CHECK(r.value().direction.y == 0.0);
    CHECK(r.value().direction.z == 1.0);
}
