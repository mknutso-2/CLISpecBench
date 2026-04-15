// Tests for §4.55 — Angular Dimension Entity (Type 202).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/angular_dimension_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.55: "Parameters: DENOTE, DEWIT1, DEWIT2, XT, YT, R, DEARRW1,
//   DEARRW2"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.55 — parse angular dimension", "[entity][spec-4.55]") {
    // §4.55: "DENOTE: Pointer to the General Note Entity"
    //        "DEWIT1, DEWIT2: Pointers to witness line entities"
    //        "XT, YT: Coordinates of vertex point"
    //        "R: Radius of leader arcs"
    //        "DEARRW1, DEARRW2: Pointers to leader entities"
    ParamTokenizer tok("1,3,5,10.0,20.0,15.0,7,9;", ',', ';');
    auto r = parse_angular_dimension_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().denote.value == 1);
    CHECK(r.value().dewit1.value == 3);
    CHECK(r.value().dewit2.value == 5);
    CHECK(r.value().xt == 10.0);
    CHECK(r.value().yt == 20.0);
    CHECK(r.value().radius == 15.0);
    CHECK(r.value().dearrw1.value == 7);
    CHECK(r.value().dearrw2.value == 9);
}
