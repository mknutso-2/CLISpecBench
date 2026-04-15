// Tests for §4.19 — Tabulated Cylinder Entity (Type 122).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/tabulated_cylinder_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.19: "Parameters: DE, LX, LY, LZ"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.19 — parse tabulated cylinder basic", "[entity][spec-4.19]") {
    // §4.19: "DE: Pointer to the DE of the directrix curve entity"
    //        "LX: X-coordinate of the terminate point of the generatrix"
    //        "LY: Y-coordinate of the terminate point of the generatrix"
    //        "LZ: Z-coordinate of the terminate point of the generatrix"
    ParamTokenizer tok("1,10.0,20.0,30.0;", ',', ';');
    auto r = parse_tabulated_cylinder_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().de.value == 1);
    CHECK(r.value().terminate_point.x == 10.0);
    CHECK(r.value().terminate_point.y == 20.0);
    CHECK(r.value().terminate_point.z == 30.0);
}

TEST_CASE("§4.19 — generatrix terminate point coordinates", "[entity][spec-4.19]") {
    // §4.19: "(LX, LY, LZ) represent the coordinates of the ...
    //   terminate point ... of the generatrix line segment."
    ParamTokenizer tok("5,0.0,0.0,100.0;", ',', ';');
    auto r = parse_tabulated_cylinder_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().terminate_point.x == 0.0);
    CHECK(r.value().terminate_point.y == 0.0);
    CHECK(r.value().terminate_point.z == 100.0);
}

TEST_CASE("§4.19 — directrix is a DE pointer", "[entity][spec-4.19]") {
    // §4.19: "DE: Pointer to the DE of the directrix curve entity"
    ParamTokenizer tok("99,1.5,2.5,3.5;", ',', ';');
    auto r = parse_tabulated_cylinder_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().de.value == 99);
}
