// Tests for §4.16 — Point Entity (Type 116).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/point_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// ─────────────────────────────────────────────────────────────────
// §4.16: "A point is a geometric entity which has a location
//   in three-dimensional space"
//   Parameters: X, Y, Z, PTR (display symbol pointer)
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.16 — parse point entity", "[entity][spec-4.16]") {
    // §4.16: "Parameters: X, Y, Z ... PTR (Pointer to DE of a
    //   display symbol geometry entity)"
    ParamTokenizer tok("1.0,2.0,3.0,0;", ',', ';');
    auto r = parse_point_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r.value().coords.x, WithinRel(1.0));
    CHECK_THAT(r.value().coords.y, WithinRel(2.0));
    CHECK_THAT(r.value().coords.z, WithinRel(3.0));
    // §4.16: "PTR ... Default = 0 (no display symbol)"
    CHECK(r.value().display_symbol.is_null());
}

TEST_CASE("§4.16 — point at origin", "[entity][spec-4.16]") {
    // §4.16: "A point ... has a location in three-dimensional space"
    ParamTokenizer tok("0.,0.,0.,0;", ',', ';');
    auto r = parse_point_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r.value().coords.x, WithinAbs(0.0, 1e-15));
}

TEST_CASE("§4.16 — point with display symbol pointer", "[entity][spec-4.16]") {
    // §4.16: "PTR = Pointer to DE of a display symbol geometry entity
    //   ... or zero. If zero, no display symbol is specified."
    ParamTokenizer tok("1.0,2.0,3.0,5;", ',', ';');
    auto r = parse_point_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().display_symbol.value == 5);
}

TEST_CASE("§4.16 — display symbol defaults to 0 when omitted", "[entity][spec-4.16]") {
    // §4.16: "PTR ... Default = 0 (no display symbol)"
    ParamTokenizer tok("1.0,2.0,3.0;", ',', ';');
    auto r = parse_point_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().display_symbol.is_null());
}
