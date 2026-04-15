// Tests for §4.52 — Right Circular Conical Surface Entity (Type 194).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/conical_surface_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.52 — parse unparameterized conical surface (Form 0)", "[entity][spec-4.52]") {
    // §4.52: "DELOC, DEAXIS, RADIUS, SANGLE"
    ParamTokenizer tok("1,3,2.0,30.0;", ',', ';');
    auto r = parse_conical_surface_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r.value().deloc.value == 1);
    CHECK(r.value().deaxis.value == 3);
    CHECK(r.value().radius == 2.0);
    CHECK(r.value().sangle == 30.0);
    CHECK(r.value().derefd.is_null());
}

TEST_CASE("§4.52 — parse parameterized conical surface (Form 1)", "[entity][spec-4.52]") {
    // §4.52: Form 1 adds "DEREFD"
    ParamTokenizer tok("1,3,2.0,30.0,9;", ',', ';');
    auto r = parse_conical_surface_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r.value().derefd.value == 9);
}
