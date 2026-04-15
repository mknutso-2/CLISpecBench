// Tests for §4.45 — Ellipsoid Entity (Type 168).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/ellipsoid_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.45 — parse ellipsoid with all parameters", "[entity][spec-4.45]") {
    // §4.45: "Parameters: LX, LY, LZ, X1, Y1, Z1, I1, J1, K1, I2, J2, K2"
    ParamTokenizer tok("10.0,8.0,5.0,1.0,2.0,3.0,1.0,0.0,0.0,0.0,0.0,1.0;", ',', ';');
    auto r = parse_ellipsoid_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().lx == 10.0);
    CHECK(r.value().ly == 8.0);
    CHECK(r.value().lz == 5.0);
    CHECK(r.value().center.x == 1.0);
    CHECK(r.value().center.y == 2.0);
    CHECK(r.value().center.z == 3.0);
}

TEST_CASE("§4.45 — ellipsoid defaults", "[entity][spec-4.45]") {
    // §4.45: "Coordinates of point in center (default (0.0,0.0,0.0))"
    //        "Unit vector defining local X-axis (default (1.0,0.0,0.0))"
    //        "Unit vector defining local Z-axis (default (0.0,0.0,1.0))"
    ParamTokenizer tok("10.0,8.0,5.0,,,,,,,,,,;", ',', ';');
    auto r = parse_ellipsoid_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().center.x == 0.0);
    CHECK(r.value().x_axis.x == 1.0);
    CHECK(r.value().z_axis.z == 1.0);
}
