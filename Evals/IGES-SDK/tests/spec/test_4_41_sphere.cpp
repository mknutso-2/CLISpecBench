// Tests for §4.41 — Sphere Entity (Type 158).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/sphere_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.41 — parse sphere", "[entity][spec-4.41]") {
    // §4.41: "Parameters: R, X1, Y1, Z1"
    ParamTokenizer tok("5.0,1.0,2.0,3.0;", ',', ';');
    auto r = parse_sphere_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().radius == 5.0);
    CHECK(r.value().center.x == 1.0);
    CHECK(r.value().center.y == 2.0);
    CHECK(r.value().center.z == 3.0);
}

TEST_CASE("§4.41 — sphere default center", "[entity][spec-4.41]") {
    // §4.41: "Center coordinates (default (0.0,0.0,0.0))"
    ParamTokenizer tok("10.0,,,;", ',', ';');
    auto r = parse_sphere_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().center.x == 0.0);
    CHECK(r.value().center.y == 0.0);
    CHECK(r.value().center.z == 0.0);
}
