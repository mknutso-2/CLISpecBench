// Tests for §4.56 — Diameter Dimension Entity (Type 206).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/diameter_dimension_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.56: "Parameters: DENOTE, DEARRW1, DEARRW2, XT, YT"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.56 — parse diameter dimension", "[entity][spec-4.56]") {
    // §4.56: "DENOTE: Pointer to General Note"
    //        "DEARRW1: Pointer to first Leader"
    //        "DEARRW2: Pointer to second Leader (or 0)"
    //        "XT, YT: Arc center coordinates"
    ParamTokenizer tok("1,3,5,10.0,20.0;", ',', ';');
    auto r = parse_diameter_dimension_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().denote.value == 1);
    CHECK(r.value().dearrw1.value == 3);
    CHECK(r.value().dearrw2.value == 5);
    CHECK(r.value().xt == 10.0);
    CHECK(r.value().yt == 20.0);
}

TEST_CASE("§4.56 — diameter dimension with single leader", "[entity][spec-4.56]") {
    // §4.56: "DEARRW2 ... or zero"
    ParamTokenizer tok("1,3,0,5.0,5.0;", ',', ';');
    auto r = parse_diameter_dimension_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().dearrw2.is_null());
}
