// Tests for §4.60 — Linear Dimension Entity (Type 216).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/linear_dimension_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.60: "Parameters: DENOTE, DEARRW1, DEARRW2, DEWIT1, DEWIT2,
//   XT, YT"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.60 — parse linear dimension", "[entity][spec-4.60]") {
    // §4.60: "DENOTE: Pointer to the General Note Entity"
    //        "DEARRW1, DEARRW2: Pointers to first/second Leader Entities"
    //        "DEWIT1, DEWIT2: Pointers to first/second Witness Line Entities (or 0)"
    //        "XT, YT: Not used (included for compatibility)"
    ParamTokenizer tok("1,3,5,7,9,0.0,0.0;", ',', ';');
    auto r = parse_linear_dimension_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().denote.value == 1);
    CHECK(r.value().dearrw1.value == 3);
    CHECK(r.value().dearrw2.value == 5);
    CHECK(r.value().dewit1.value == 7);
    CHECK(r.value().dewit2.value == 9);
}

TEST_CASE("§4.60 — linear dimension without witness lines", "[entity][spec-4.60]") {
    // §4.60: "DEWIT1, DEWIT2 ... or zero"
    ParamTokenizer tok("1,3,5,0,0,0.0,0.0;", ',', ';');
    auto r = parse_linear_dimension_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().dewit1.is_null());
    CHECK(r.value().dewit2.is_null());
}
