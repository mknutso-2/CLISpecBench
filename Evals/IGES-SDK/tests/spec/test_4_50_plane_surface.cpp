// Tests for §4.50 — Plane Surface Entity (Type 190).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/plane_surface_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.50 — parse unparameterized plane surface (Form 0)", "[entity][spec-4.50]") {
    // §4.50: "DELOC: Pointer to the DE of the point on the surface"
    //        "DENRML: Pointer to the DE of the surface normal direction"
    ParamTokenizer tok("1,3;", ',', ';');
    auto r = parse_plane_surface_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r.value().deloc.value == 1);
    CHECK(r.value().denrml.value == 3);
    CHECK(r.value().derefd.is_null());
}

TEST_CASE("§4.50 — parse parameterized plane surface (Form 1)", "[entity][spec-4.50]") {
    // §4.50: Form 1 adds "DEREFD: Pointer to the DE of the reference direction"
    ParamTokenizer tok("1,3,5;", ',', ';');
    auto r = parse_plane_surface_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r.value().deloc.value == 1);
    CHECK(r.value().denrml.value == 3);
    CHECK(r.value().derefd.value == 5);
}
