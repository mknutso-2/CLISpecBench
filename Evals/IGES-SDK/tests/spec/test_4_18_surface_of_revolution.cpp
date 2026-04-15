// Tests for §4.18 — Surface of Revolution Entity (Type 120).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/surface_of_revolution_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.18: "Parameters: L, C, SA, TA"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.18 — parse surface of revolution basic", "[entity][spec-4.18]") {
    // §4.18: "L: Pointer to the DE of the Line Entity (axis of revolution)"
    //        "C: Pointer to the DE of the generatrix entity"
    //        "SA: Start angle in radians"
    //        "TA: Terminate angle in radians"
    ParamTokenizer tok("1,3,0.0,6.283185;", ',', ';');
    auto r = parse_surface_of_revolution_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().l.value == 1);
    CHECK(r.value().c.value == 3);
    CHECK(r.value().sa == 0.0);
    CHECK(r.value().ta == 6.283185);
}

TEST_CASE("§4.18 — partial revolution", "[entity][spec-4.18]") {
    // §4.18: "SA and TA are constrained so that 0 < TA - SA <= 2*pi"
    ParamTokenizer tok("5,7,0.5,3.14159;", ',', ';');
    auto r = parse_surface_of_revolution_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().sa == 0.5);
    CHECK(r.value().ta == 3.14159);
}

TEST_CASE("§4.18 — axis and generatrix are DE pointers", "[entity][spec-4.18]") {
    // §4.18: "L: Pointer to the DE of the Line Entity"
    //        "C: Pointer to the DE of the generatrix entity"
    ParamTokenizer tok("11,13,0.0,1.5708;", ',', ';');
    auto r = parse_surface_of_revolution_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().l.value == 11);
    CHECK(r.value().c.value == 13);
}
