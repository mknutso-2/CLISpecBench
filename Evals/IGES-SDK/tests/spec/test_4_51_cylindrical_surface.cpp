// Tests for §4.51 — Right Circular Cylindrical Surface Entity (Type 192).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/cylindrical_surface_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.51 — parse unparameterized cylindrical surface (Form 0)", "[entity][spec-4.51]") {
    // §4.51: "DELOC, DEAXIS, RADIUS"
    ParamTokenizer tok("1,3,5.0;", ',', ';');
    auto r = parse_cylindrical_surface_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r.value().deloc.value == 1);
    CHECK(r.value().deaxis.value == 3);
    CHECK(r.value().radius == 5.0);
    CHECK(r.value().derefd.is_null());
}

TEST_CASE("§4.51 — parse parameterized cylindrical surface (Form 1)", "[entity][spec-4.51]") {
    // §4.51: Form 1 adds "DEREFD"
    ParamTokenizer tok("1,3,5.0,7;", ',', ';');
    auto r = parse_cylindrical_surface_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r.value().derefd.value == 7);
}
