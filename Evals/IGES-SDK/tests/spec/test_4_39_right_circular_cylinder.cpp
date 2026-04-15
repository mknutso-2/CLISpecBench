// Tests for §4.39 — Right Circular Cylinder Entity (Type 154).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/right_circular_cylinder_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.39 — parse right circular cylinder", "[entity][spec-4.39]") {
    // §4.39: "Parameters: H, R, X1, Y1, Z1, I1, J1, K1"
    ParamTokenizer tok("10.0,5.0,0.0,0.0,0.0,0.0,0.0,1.0;", ',', ';');
    auto r = parse_right_circular_cylinder_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().h == 10.0);
    CHECK(r.value().r == 5.0);
    CHECK(r.value().face_center.x == 0.0);
    CHECK(r.value().axis.z == 1.0);
}

TEST_CASE("§4.39 — cylinder defaults", "[entity][spec-4.39]") {
    // §4.39: "First face center coordinates (default (0.0,0.0,0.0))"
    //        "Unit vector in axis direction (default (0.0,0.0,1.0))"
    ParamTokenizer tok("3.0,1.5,,,,,,;", ',', ';');
    auto r = parse_right_circular_cylinder_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().face_center.x == 0.0);
    CHECK(r.value().face_center.y == 0.0);
    CHECK(r.value().face_center.z == 0.0);
    CHECK(r.value().axis.x == 0.0);
    CHECK(r.value().axis.y == 0.0);
    CHECK(r.value().axis.z == 1.0);
}
