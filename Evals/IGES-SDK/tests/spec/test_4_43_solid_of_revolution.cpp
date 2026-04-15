// Tests for §4.43 — Solid of Revolution Entity (Type 162).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/solid_of_revolution_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.43 — parse solid of revolution", "[entity][spec-4.43]") {
    // §4.43: "Parameters: PTR, F, X1, Y1, Z1, I1, J1, K1"
    ParamTokenizer tok("3,0.5,0.0,0.0,0.0,0.0,0.0,1.0;", ',', ';');
    auto r = parse_solid_of_revolution_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().ptr.value == 3);
    CHECK(r.value().f == 0.5);
    CHECK(r.value().axis_point.x == 0.0);
    CHECK(r.value().axis_dir.z == 1.0);
}

TEST_CASE("§4.43 — solid of revolution defaults", "[entity][spec-4.43]") {
    // §4.43: "F: Fraction of full rotation ... default 1"
    //        "Coordinates of point on axis (default (0.0,0.0,0.0))"
    //        "Unit vector in axis direction (default (0.0,0.0,1.0))"
    ParamTokenizer tok("5,,,,,,,;", ',', ';');
    auto r = parse_solid_of_revolution_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().f == 1.0);
    CHECK(r.value().axis_point.x == 0.0);
    CHECK(r.value().axis_dir.z == 1.0);
}
