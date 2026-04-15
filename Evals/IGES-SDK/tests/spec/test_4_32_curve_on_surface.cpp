// Tests for §4.32 — Curve on a Parametric Surface Entity (Type 142).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/curve_on_surface_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.32: "Parameters: CRTN, SPTR, BPTR, CPTR, PREF"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.32 — parse curve on parametric surface", "[entity][spec-4.32]") {
    // §4.32: "Parameters: CRTN, SPTR, BPTR, CPTR, PREF"
    //   CRTN=1 (projection), SPTR=5, BPTR=7, CPTR=9, PREF=2 (C preferred)
    ParamTokenizer tok("1,5,7,9,2;", ',', ';');
    auto r = parse_curve_on_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().crtn == 1);
    CHECK(r.value().sptr.value == 5);
    CHECK(r.value().bptr.value == 7);
    CHECK(r.value().cptr.value == 9);
    CHECK(r.value().pref == 2);
}

// ─────────────────────────────────────────────────────────────────
// §4.32: "CRTN: Indicates the way the curve on the surface has
//   been created: 0=Unspecified, 1=Projection, 2=Intersection,
//   3=Isoparametric"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.32 — CRTN=0 unspecified creation method", "[entity][spec-4.32]") {
    // §4.32: "0 = Unspecified"
    ParamTokenizer tok("0,1,3,5,0;", ',', ';');
    auto r = parse_curve_on_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().crtn == 0);
}

TEST_CASE("§4.32 — CRTN=2 intersection of two surfaces", "[entity][spec-4.32]") {
    // §4.32: "2 = Intersection of two surfaces"
    ParamTokenizer tok("2,1,3,5,1;", ',', ';');
    auto r = parse_curve_on_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().crtn == 2);
}

TEST_CASE("§4.32 — CRTN=3 isoparametric curve", "[entity][spec-4.32]") {
    // §4.32: "3 = Isoparametric curve, i.e., either a u-parametric
    //   or a v-parametric curve"
    ParamTokenizer tok("3,1,3,5,3;", ',', ';');
    auto r = parse_curve_on_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().crtn == 3);
}

// ─────────────────────────────────────────────────────────────────
// §4.32: "PREF: 0=Unspecified, 1=S∘B is preferred, 2=C is
//   preferred, 3=C and S∘B are equally preferred"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.32 — PREF=1 S∘B preferred", "[entity][spec-4.32]") {
    // §4.32: "1 = S∘B is preferred"
    ParamTokenizer tok("0,1,3,5,1;", ',', ';');
    auto r = parse_curve_on_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().pref == 1);
}

TEST_CASE("§4.32 — PREF=3 equally preferred", "[entity][spec-4.32]") {
    // §4.32: "3 = C and S∘B are equally preferred"
    ParamTokenizer tok("0,1,3,5,3;", ',', ';');
    auto r = parse_curve_on_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().pref == 3);
}
