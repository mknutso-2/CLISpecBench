// Tests for §4.17 — Ruled Surface Entity (Type 118).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/ruled_surface_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.17: "Parameters: DE1, DE2, DIRFLG, DEVFLG"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.17 — parse ruled surface basic", "[entity][spec-4.17]") {
    // §4.17: "DE1: Pointer to the DE of the first curve entity"
    //        "DE2: Pointer to the DE of the second curve entity"
    //        "DIRFLG: Direction flag"
    //        "DEVFLG: Developable surface flag"
    ParamTokenizer tok("1,3,0,0;", ',', ';');
    auto r = parse_ruled_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().de1.value == 1);
    CHECK(r.value().de2.value == 3);
    CHECK(r.value().dirflg == 0);
    CHECK(r.value().devflg == 0);
}

TEST_CASE("§4.17 — DIRFLG=0 first-to-first", "[entity][spec-4.17]") {
    // §4.17: "If DIRFLG=0, the first point of curve 1 is joined to
    //   the first point of curve 2, and the last point of curve 1
    //   to last point of curve 2."
    ParamTokenizer tok("5,7,0,1;", ',', ';');
    auto r = parse_ruled_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().dirflg == 0);
}

TEST_CASE("§4.17 — DIRFLG=1 first-to-last", "[entity][spec-4.17]") {
    // §4.17: "If DIRFLG=1, the first point of curve 1 is joined to
    //   the last point of curve 2, and the last point of curve 1
    //   to the first point of curve 2."
    ParamTokenizer tok("5,7,1,0;", ',', ';');
    auto r = parse_ruled_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().dirflg == 1);
}

TEST_CASE("§4.17 — DEVFLG=1 developable", "[entity][spec-4.17]") {
    // §4.17: "If DEVFLG=1, the surface is a developable surface;
    //   if DEVFLG=0, the surface may or may not be a developable surface."
    ParamTokenizer tok("1,3,0,1;", ',', ';');
    auto r = parse_ruled_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().devflg == 1);
}
