// Tests for §4.24 — Rational B-Spline Surface Entity (Type 128).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/rational_bspline_surface_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// ─────────────────────────────────────────────────────────────────
// Helper: bilinear patch (degree 1x1)
//   K1=1, K2=1, M1=1, M2=1
//   N1=1, N2=1, A=3, B=3
//   Knots_u: [0,0,1,1], Knots_v: [0,0,1,1]
//   C = (1+1)*(1+1) = 4
//   Weights: [1,1,1,1]
//   Control points (first index varies fastest):
//     (0,0) → (0,0,0)  (1,0) → (1,0,0)
//     (0,1) → (0,1,0)  (1,1) → (1,1,0)
// ─────────────────────────────────────────────────────────────────
static const char* kBilinearPatch =
    "1,1,1,1,"                              // K1,K2,M1,M2
    "0,0,1,0,0,"                            // PROP1-5
    "0.,0.,1.,1.,"                          // knots_u (A+1=4)
    "0.,0.,1.,1.,"                          // knots_v (B+1=4)
    "1.,1.,1.,1.,"                          // weights (C=4)
    "0.,0.,0.,"                             // P(0,0) = (0,0,0)
    "1.,0.,0.,"                             // P(1,0) = (1,0,0)
    "0.,1.,0.,"                             // P(0,1) = (0,1,0)
    "1.,1.,0.,"                             // P(1,1) = (1,1,0)
    "0.,1.,0.,1.;";                         // U(0),U(1),V(0),V(1)

// ─────────────────────────────────────────────────────────────────
// §4.24: "Parameters: K1, K2, M1, M2, PROP1-5, two knot vectors,
//   weights grid, control points grid, U/V ranges"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.24 — parse bilinear B-spline surface", "[entity][spec-4.24]") {
    // §4.24: "Parameters: K1, K2, M1, M2, PROP1-5, ..."
    ParamTokenizer tok(kBilinearPatch, ',', ';');
    auto r = parse_rational_bspline_surface_entity(tok);
    REQUIRE(r.has_value());
    auto& s = r.value();
    CHECK(s.K1 == 1);
    CHECK(s.K2 == 1);
    CHECK(s.M1 == 1);
    CHECK(s.M2 == 1);
    CHECK(s.prop1 == 0);
    CHECK(s.prop2 == 0);
    CHECK(s.prop3 == 1);  // polynomial
    CHECK(s.prop4 == 0);
    CHECK(s.prop5 == 0);
}

// ─────────────────────────────────────────────────────────────────
// §4.24: "N1=1+K1-M1, N2=1+K2-M2, A=N1+2*M1, B=N2+2*M2,
//   C=(1+K1)*(1+K2)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.24 — length invariants", "[entity][spec-4.24]") {
    // §4.24: "Let N1 = 1 + K1 - M1, N2 = 1 + K2 - M2,
    //   A = N1 + 2*M1, B = N2 + 2*M2, and C = (1 + K1)*(1 + K2)"
    ParamTokenizer tok(kBilinearPatch, ',', ';');
    auto r = parse_rational_bspline_surface_entity(tok);
    REQUIRE(r.has_value());
    auto& s = r.value();
    CHECK(s.N1() == 1);
    CHECK(s.N2() == 1);
    CHECK(s.A() == 3);
    CHECK(s.B() == 3);
    CHECK(s.C() == 4);
    CHECK(s.knots_u.size() == 4);   // A+1
    CHECK(s.knots_v.size() == 4);   // B+1
    CHECK(s.weights.size() == 4);   // C
    CHECK(s.control_points.size() == 4);  // C
}

// ─────────────────────────────────────────────────────────────────
// §4.24: "Weights stored as W(0,0),W(1,0),...,W(K1,K2) —
//   first index varies fastest"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.24 — weight storage order: first index varies fastest", "[entity][spec-4.24]") {
    // §4.24: "W(0,0), W(1,0), ..., W(K1,0), W(0,1), ..., W(K1,K2)"
    ParamTokenizer tok(kBilinearPatch, ',', ';');
    auto r = parse_rational_bspline_surface_entity(tok);
    REQUIRE(r.has_value());
    // All weights are 1.0 in this test; verify access works
    CHECK(r.value().weight(0, 0) == 1.0);
    CHECK(r.value().weight(1, 0) == 1.0);
    CHECK(r.value().weight(0, 1) == 1.0);
    CHECK(r.value().weight(1, 1) == 1.0);
}

// ─────────────────────────────────────────────────────────────────
// §4.24: "Control points stored in same order as weights"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.24 — control point storage order", "[entity][spec-4.24]") {
    // §4.24: "Control points stored in same order as weights"
    ParamTokenizer tok(kBilinearPatch, ',', ';');
    auto r = parse_rational_bspline_surface_entity(tok);
    REQUIRE(r.has_value());
    auto& s = r.value();
    // P(0,0) = (0,0,0)
    CHECK_THAT(s.control_point(0, 0).x, WithinAbs(0.0, 1e-15));
    CHECK_THAT(s.control_point(0, 0).y, WithinAbs(0.0, 1e-15));
    // P(1,0) = (1,0,0)
    CHECK_THAT(s.control_point(1, 0).x, WithinRel(1.0));
    CHECK_THAT(s.control_point(1, 0).y, WithinAbs(0.0, 1e-15));
    // P(0,1) = (0,1,0)
    CHECK_THAT(s.control_point(0, 1).x, WithinAbs(0.0, 1e-15));
    CHECK_THAT(s.control_point(0, 1).y, WithinRel(1.0));
    // P(1,1) = (1,1,0)
    CHECK_THAT(s.control_point(1, 1).x, WithinRel(1.0));
    CHECK_THAT(s.control_point(1, 1).y, WithinRel(1.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.24: Parameter ranges
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.24 — parameter ranges parsed", "[entity][spec-4.24]") {
    // §4.24: "U(0), U(1), V(0), V(1)" — starting/ending values
    ParamTokenizer tok(kBilinearPatch, ',', ';');
    auto r = parse_rational_bspline_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r.value().u0, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r.value().u1, WithinRel(1.0));
    CHECK_THAT(r.value().v0, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r.value().v1, WithinRel(1.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.24: Evaluation — bilinear patch corners
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.24 — evaluate bilinear patch at corners", "[entity][spec-4.24]") {
    // §4.24: Bilinear surface evaluation at four corners
    ParamTokenizer tok(kBilinearPatch, ',', ';');
    auto r = parse_rational_bspline_surface_entity(tok);
    REQUIRE(r.has_value());
    auto& s = r.value();

    // (0,0) → P(0,0) = (0,0,0)
    auto p00 = s.evaluate(0.0, 0.0);
    CHECK_THAT(p00.x, WithinAbs(0.0, 1e-10));
    CHECK_THAT(p00.y, WithinAbs(0.0, 1e-10));

    // (1,0) → P(1,0) = (1,0,0)
    auto p10 = s.evaluate(1.0, 0.0);
    CHECK_THAT(p10.x, WithinRel(1.0));
    CHECK_THAT(p10.y, WithinAbs(0.0, 1e-10));

    // (0,1) → P(0,1) = (0,1,0)
    auto p01 = s.evaluate(0.0, 1.0);
    CHECK_THAT(p01.x, WithinAbs(0.0, 1e-10));
    CHECK_THAT(p01.y, WithinRel(1.0));

    // (1,1) → P(1,1) = (1,1,0)
    auto p11 = s.evaluate(1.0, 1.0);
    CHECK_THAT(p11.x, WithinRel(1.0));
    CHECK_THAT(p11.y, WithinRel(1.0));
}

TEST_CASE("§4.24 — evaluate bilinear patch at center", "[entity][spec-4.24]") {
    // §4.24: Bilinear interpolation at (0.5, 0.5) → (0.5, 0.5, 0)
    ParamTokenizer tok(kBilinearPatch, ',', ';');
    auto r = parse_rational_bspline_surface_entity(tok);
    REQUIRE(r.has_value());
    auto mid = r.value().evaluate(0.5, 0.5);
    CHECK_THAT(mid.x, WithinRel(0.5));
    CHECK_THAT(mid.y, WithinRel(0.5));
    CHECK_THAT(mid.z, WithinAbs(0.0, 1e-10));
}

// ─────────────────────────────────────────────────────────────────
// §4.24: "The weights shall be positive real numbers"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.24 — all weights are positive", "[entity][spec-4.24]") {
    // §4.24: "The weights shall be positive real numbers"
    ParamTokenizer tok(kBilinearPatch, ',', ';');
    auto r = parse_rational_bspline_surface_entity(tok);
    REQUIRE(r.has_value());
    for (auto w : r.value().weights) {
        CHECK(w > 0.0);
    }
}
