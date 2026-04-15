// Tests for §4.37 — Block Entity (Type 150).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/block_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.37 — parse block with all parameters", "[entity][spec-4.37]") {
    // §4.37: "Parameters: LX, LY, LZ, X1, Y1, Z1, I1, J1, K1, I2, J2, K2"
    ParamTokenizer tok("10.0,20.0,30.0,1.0,2.0,3.0,1.0,0.0,0.0,0.0,0.0,1.0;", ',', ';');
    auto r = parse_block_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().lx == 10.0);
    CHECK(r.value().ly == 20.0);
    CHECK(r.value().lz == 30.0);
    CHECK(r.value().corner.x == 1.0);
    CHECK(r.value().corner.y == 2.0);
    CHECK(r.value().corner.z == 3.0);
    CHECK(r.value().x_axis.x == 1.0);
    CHECK(r.value().z_axis.z == 1.0);
}

TEST_CASE("§4.37 — block defaults", "[entity][spec-4.37]") {
    // §4.37: "Corner point coordinates (default (0.0,0.0,0.0))"
    //        "Unit vector defining local X-axis (default (1.0,0.0,0.0))"
    //        "Unit vector defining local Z-axis (default (0.0,0.0,1.0))"
    ParamTokenizer tok("5.0,5.0,5.0,,,,,,,,,,;", ',', ';');
    auto r = parse_block_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().corner.x == 0.0);
    CHECK(r.value().corner.y == 0.0);
    CHECK(r.value().corner.z == 0.0);
    CHECK(r.value().x_axis.x == 1.0);
    CHECK(r.value().x_axis.y == 0.0);
    CHECK(r.value().x_axis.z == 0.0);
    CHECK(r.value().z_axis.x == 0.0);
    CHECK(r.value().z_axis.y == 0.0);
    CHECK(r.value().z_axis.z == 1.0);
}
