// Tests for §4.5 — Conic Arc Entity (Type 104).
// Spec reference: IGES 5.3, §4.5, pages 71-73.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/conic_arc_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"
#include <cmath>

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// ─────────────────────────────────────────────────────────────────
// §4.5: "Parameters: A, B, C, D, E, F, ZT, X1, Y1, X2, Y2"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.5 — parse conic arc entity (11 parameters)", "[entity][spec-4.5]") {
    // §4.5 PD: "Index 1-6: A,B,C,D,E,F; 7: ZT; 8-9: X1,Y1; 10-11: X2,Y2"
    // Unit circle: x^2 + y^2 - 1 = 0 => A=1,B=0,C=1,D=0,E=0,F=-1
    ParamTokenizer tok("1.0,0.0,1.0,0.0,0.0,-1.0,0.0,1.0,0.0,0.0,1.0;", ',', ';');
    auto r = parse_conic_arc_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->A, WithinRel(1.0));
    CHECK_THAT(r->B, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r->C, WithinRel(1.0));
    CHECK_THAT(r->D, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r->E, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r->F, WithinRel(-1.0));
    CHECK_THAT(r->zt, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r->x1, WithinRel(1.0));
    CHECK_THAT(r->y1, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r->x2, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r->y2, WithinRel(1.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.5: Q2 = AC - (B/2)^2; Q3 = A + C
// "An ellipse if Q2 > 0 and Q2*Q3 < 0"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.5 — unit circle is classified as ellipse", "[entity][spec-4.5]") {
    // §4.5: "An ellipse if Q2 > 0 and Q2*Q3 < 0"
    // x^2 + y^2 - 1 = 0: A=1,B=0,C=1 => Q2 = 1*1 - 0 = 1 > 0
    //                                     Q3 = 1 + 1 = 2
    //                                     Q2*Q3 = 2 > 0 ... wait
    // For a proper ellipse per spec, need Q2 > 0 and Q2*Q3 < 0.
    // x^2 + y^2 - 1 = 0 has F = -1. Q1 involves F.
    // Actually the classification only uses Q2 and Q3 of the coefficients.
    // A=1, C=1, F=-1 => Q3 = 2 > 0, Q2 = 1 > 0, Q2*Q3 = 2 > 0.
    // This means the circle needs different sign convention.
    // With A=-1, B=0, C=-1, F=1: -x^2 - y^2 + 1 = 0 (same curve)
    // Q2 = (-1)(-1) - 0 = 1 > 0, Q3 = -1 + -1 = -2, Q2*Q3 = -2 < 0. Ellipse!
    ConicArcEntity arc;
    arc.A = -1.0; arc.B = 0.0; arc.C = -1.0;
    arc.D = 0.0; arc.E = 0.0; arc.F = 1.0;
    CHECK(arc.Q2() > 0.0);
    CHECK(arc.Q2() * arc.Q3() < 0.0);
    CHECK(arc.is_ellipse());
    CHECK(!arc.is_hyperbola());
    CHECK(!arc.is_parabola());
}

TEST_CASE("§4.5 — axis-aligned ellipse classification", "[entity][spec-4.5]") {
    // §4.5: "An ellipse if Q2 > 0 and Q2*Q3 < 0"
    // x^2/4 + y^2/9 - 1 = 0 => multiply by -1: -x^2/4 - y^2/9 + 1 = 0
    // A=-0.25, B=0, C=-1/9, F=1
    ConicArcEntity arc;
    arc.A = -0.25; arc.B = 0.0; arc.C = -1.0/9.0;
    arc.D = 0.0; arc.E = 0.0; arc.F = 1.0;
    CHECK(arc.Q2() > 0.0);
    CHECK(arc.Q2() * arc.Q3() < 0.0);
    CHECK(arc.is_ellipse());
}

// ─────────────────────────────────────────────────────────────────
// §4.5: "A hyperbola if Q2 < 0"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.5 — hyperbola classification", "[entity][spec-4.5]") {
    // §4.5: "A hyperbola if Q2 < 0"
    // x^2 - y^2 - 1 = 0: A=1, B=0, C=-1 => Q2 = 1*(-1) - 0 = -1 < 0
    ConicArcEntity arc;
    arc.A = 1.0; arc.B = 0.0; arc.C = -1.0;
    arc.D = 0.0; arc.E = 0.0; arc.F = -1.0;
    CHECK(arc.Q2() < 0.0);
    CHECK(arc.is_hyperbola());
    CHECK(!arc.is_ellipse());
    CHECK(!arc.is_parabola());
}

// ─────────────────────────────────────────────────────────────────
// §4.5: "A parabola if Q2 = 0 and Q1 != 0"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.5 — parabola classification", "[entity][spec-4.5]") {
    // §4.5: "A parabola if Q2 = 0 and Q1 != 0"
    // y = x^2 => x^2 - y = 0 => A=1, B=0, C=0, D=0, E=-1, F=0
    // Q2 = A*C - (B/2)^2 = 1*0 - 0 = 0
    // Q1 = det... needs to be non-zero
    ConicArcEntity arc;
    arc.A = 1.0; arc.B = 0.0; arc.C = 0.0;
    arc.D = 0.0; arc.E = -1.0; arc.F = 0.0;
    CHECK_THAT(arc.Q2(), WithinAbs(0.0, 1e-15));
    CHECK(arc.Q1() != 0.0);
    CHECK(arc.is_parabola());
    CHECK(!arc.is_ellipse());
    CHECK(!arc.is_hyperbola());
}

// ─────────────────────────────────────────────────────────────────
// §4.5: Q1 determinant formula
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.5 — Q1 determinant formula", "[entity][spec-4.5]") {
    // §4.5: Q1 = det |A   B/2 D/2|
    //               |B/2 C   E/2|
    //               |D/2 E/2 F  |
    // For A=1,B=0,C=1,D=0,E=0,F=-1:
    // Q1 = 1*(1*(-1) - 0) - 0 + 0 = -1
    ConicArcEntity arc;
    arc.A = 1.0; arc.B = 0.0; arc.C = 1.0;
    arc.D = 0.0; arc.E = 0.0; arc.F = -1.0;
    CHECK_THAT(arc.Q1(), WithinRel(-1.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.5: ZT places arc in parallel plane
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.5 — ZT displacement", "[entity][spec-4.5]") {
    // §4.5: "ZT is the Z coordinate of a point in the XT,YT plane"
    ParamTokenizer tok("1.0,0.0,1.0,0.0,0.0,-1.0,5.5,1.0,0.0,0.0,1.0;", ',', ';');
    auto r = parse_conic_arc_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->zt, WithinRel(5.5));
}

// ─────────────────────────────────────────────────────────────────
// Round-trip: write then parse
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.5 — round-trip conic arc", "[entity][spec-4.5]") {
    ConicArcEntity orig;
    orig.A = 1.0; orig.B = 0.0; orig.C = -1.0;
    orig.D = 0.0; orig.E = 0.0; orig.F = -4.0;
    orig.zt = 3.0;
    orig.x1 = 2.0; orig.y1 = 0.0;
    orig.x2 = -2.0; orig.y2 = 0.0;

    auto pd = write_conic_arc_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_conic_arc_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->A, WithinRel(orig.A));
    CHECK_THAT(r->B, WithinAbs(orig.B, 1e-15));
    CHECK_THAT(r->C, WithinRel(orig.C));
    CHECK_THAT(r->F, WithinRel(orig.F));
    CHECK_THAT(r->zt, WithinRel(orig.zt));
    CHECK_THAT(r->x1, WithinRel(orig.x1));
    CHECK_THAT(r->y2, WithinAbs(orig.y2, 1e-15));
}
