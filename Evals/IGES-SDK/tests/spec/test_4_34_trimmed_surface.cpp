// Tests for §4.34 — Trimmed (Parametric) Surface Entity (Type 144).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/trimmed_surface_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.34: "Parameters: PTS, N1, N2, PTO, PTI(1)..PTI(N2)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.34 — parse trimmed surface with no inner boundaries", "[entity][spec-4.34]") {
    // §4.34: "PTS, N1, N2, PTO"
    //   PTS=1 (surface DE), N1=1 (outer boundary specified), N2=0, PTO=3
    ParamTokenizer tok("1,1,0,3;", ',', ';');
    auto r = parse_trimmed_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().pts.value == 1);
    CHECK(r.value().n1 == 1);
    CHECK(r.value().n2 == 0);
    CHECK(r.value().pto.value == 3);
    CHECK(r.value().pti.empty());
}

// ─────────────────────────────────────────────────────────────────
// §4.34: "N1=0: the outer boundary is the boundary of D"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.34 — N1=0 outer boundary defaults to parameter rectangle", "[entity][spec-4.34]") {
    // §4.34: "0 = the outer boundary is the boundary of D"
    //   PTS=1, N1=0, N2=0, PTO=0 (no outer boundary entity needed)
    ParamTokenizer tok("1,0,0,0;", ',', ';');
    auto r = parse_trimmed_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n1 == 0);
    CHECK(r.value().pto.is_null());
}

// ─────────────────────────────────────────────────────────────────
// §4.34: "N1=1: outer boundary specified by PTO (Curve on
//   Parametric Surface)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.34 — N1=1 with specified outer boundary", "[entity][spec-4.34]") {
    // §4.34: "1 = otherwise" (outer boundary given by PTO)
    ParamTokenizer tok("5,1,0,7;", ',', ';');
    auto r = parse_trimmed_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n1 == 1);
    CHECK(r.value().pto.value == 7);
}

// ─────────────────────────────────────────────────────────────────
// §4.34: "N2: number of simple closed curves which constitute
//   the inner boundary"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.34 — parse trimmed surface with 2 inner boundaries", "[entity][spec-4.34]") {
    // §4.34: "N2 ... indicates the number of simple closed curves"
    //   PTS=1, N1=1, N2=2, PTO=3, PTI(1)=5, PTI(2)=7
    ParamTokenizer tok("1,1,2,3,5,7;", ',', ';');
    auto r = parse_trimmed_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n2 == 2);
    REQUIRE(r.value().pti.size() == 2);
    CHECK(r.value().pti[0].value == 5);
    CHECK(r.value().pti[1].value == 7);
}

TEST_CASE("§4.34 — parse trimmed surface with 3 inner boundaries", "[entity][spec-4.34]") {
    // §4.34: Verify N2=3 inner boundaries
    ParamTokenizer tok("1,1,3,3,5,7,9;", ',', ';');
    auto r = parse_trimmed_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n2 == 3);
    REQUIRE(r.value().pti.size() == 3);
    CHECK(r.value().pti[2].value == 9);
}

// ─────────────────────────────────────────────────────────────────
// §4.34: "If the outer boundary ... is the boundary of D and
//   there are no inner boundaries, the trimmed surface ... is
//   untrimmed"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.34 — N1=0, N2=0 means surface is untrimmed", "[entity][spec-4.34]") {
    // §4.34: "If the outer boundary of the surface being defined is
    //   the boundary of D and there are no inner boundaries, the
    //   trimmed surface being defined is untrimmed."
    ParamTokenizer tok("1,0,0,0;", ',', ';');
    auto r = parse_trimmed_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n1 == 0);
    CHECK(r.value().n2 == 0);
    CHECK(r.value().pto.is_null());
    CHECK(r.value().pti.empty());
}
