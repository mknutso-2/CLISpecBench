// Tests for §4.54 — Toroidal Surface Entity (Type 198).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/toroidal_surface_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.54 — parse unparameterized toroidal surface (Form 0)", "[entity][spec-4.54]") {
    // §4.54: "DELOC, DEAXIS, MAJRAD, MINRAD"
    ParamTokenizer tok("1,3,10.0,2.0;", ',', ';');
    auto r = parse_toroidal_surface_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r.value().deloc.value == 1);
    CHECK(r.value().deaxis.value == 3);
    CHECK(r.value().majrad == 10.0);
    CHECK(r.value().minrad == 2.0);
    CHECK(r.value().derefd.is_null());
}

TEST_CASE("§4.54 — parse parameterized toroidal surface (Form 1)", "[entity][spec-4.54]") {
    // §4.54: Form 1 adds "DEREFD"
    ParamTokenizer tok("1,3,10.0,2.0,9;", ',', ';');
    auto r = parse_toroidal_surface_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r.value().derefd.value == 9);
}
