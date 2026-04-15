// Tests for §4.53 — Spherical Surface Entity (Type 196).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/spherical_surface_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.53 — parse unparameterized spherical surface (Form 0)", "[entity][spec-4.53]") {
    // §4.53: "DELOC: Pointer to center point"
    //        "RADIUS: Value of radius"
    ParamTokenizer tok("1,5.0;", ',', ';');
    auto r = parse_spherical_surface_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r.value().deloc.value == 1);
    CHECK(r.value().radius == 5.0);
    CHECK(r.value().deaxis.is_null());
}

TEST_CASE("§4.53 — parse parameterized spherical surface (Form 1)", "[entity][spec-4.53]") {
    // §4.53: Form 1 adds "DEAXIS, DEREFD"
    ParamTokenizer tok("1,5.0,3,7;", ',', ';');
    auto r = parse_spherical_surface_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r.value().deaxis.value == 3);
    CHECK(r.value().derefd.value == 7);
}
