// Tests for §4.23 — Rational B-Spline Curve Entity (Type 126).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/rational_bspline_curve_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include <cmath>

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// ─────────────────────────────────────────────────────────────────
// Helper: build a PD string for a cubic Bezier curve (degree 3)
//   K=3, M=3 → N=1+3-3=1, A=1+2*3=7
//   Knot vector: [0,0,0,0,1,1,1,1] (A+1 = 8 values)
//   Weights: [1,1,1,1] (K+1 = 4 values)
//   Control points: (0,0,0),(1,1,0),(2,1,0),(3,0,0)
//   V(0)=0, V(1)=1, plane normal: (0,0,1)
// ─────────────────────────────────────────────────────────────────
static const char* kCubicBezier =
    "3,3,"                                  // K=3, M=3
    "1,0,1,0,"                              // PROP1=planar, PROP2=open, PROP3=poly, PROP4=nonperiodic
    "0.,0.,0.,0.,1.,1.,1.,1.,"              // 8 knots
    "1.,1.,1.,1.,"                          // 4 weights (all equal → polynomial)
    "0.,0.,0.,"                             // P0 = (0,0,0)
    "1.,1.,0.,"                             // P1 = (1,1,0)
    "2.,1.,0.,"                             // P2 = (2,1,0)
    "3.,0.,0.,"                             // P3 = (3,0,0)
    "0.,1.,"                                // V(0)=0, V(1)=1
    "0.,0.,1.;";                            // plane normal = (0,0,1)

// ─────────────────────────────────────────────────────────────────
// §4.23: "Parameters: K, M, PROP1-4, knots, weights, control
//   points, V(0), V(1), plane normal"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.23 — parse cubic Bezier B-spline curve", "[entity][spec-4.23]") {
    // §4.23: "Parameters: K, M, PROP1-4, knots, weights, control
    //   points, V(0), V(1), plane normal"
    ParamTokenizer tok(kCubicBezier, ',', ';');
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());
    auto& c = r.value();
    CHECK(c.K == 3);
    CHECK(c.M == 3);
    CHECK(c.prop1 == 1);  // planar
    CHECK(c.prop2 == 0);  // open
    CHECK(c.prop3 == 1);  // polynomial
    CHECK(c.prop4 == 0);  // nonperiodic
}

// ─────────────────────────────────────────────────────────────────
// §4.23: "N = 1+K-M, A = N+2*M; knot vector length = A+1"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.23 — knot vector length = A+1", "[entity][spec-4.23]") {
    // §4.23: "Let N = 1 + K - M and A = N + 2*M"
    //   For K=3, M=3: N=1, A=7 → knot vector length = 8
    ParamTokenizer tok(kCubicBezier, ',', ';');
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().N() == 1);
    CHECK(r.value().A() == 7);
    CHECK(r.value().knots.size() == 8);  // A+1
}

TEST_CASE("§4.23 — knot vector length for linear B-spline", "[entity][spec-4.23]") {
    // §4.23: K=2, M=1 → N=2, A=4 → knots length = 5
    //   Knots: [0,0,0.5,1,1], Weights: [1,1,1]
    //   Control points: (0,0,0),(1,0,0),(2,0,0)
    const char* data =
        "2,1,"
        "0,0,1,0,"
        "0.,0.,0.5,1.,1.,"
        "1.,1.,1.,"
        "0.,0.,0.,"
        "1.,0.,0.,"
        "2.,0.,0.,"
        "0.,1.,"
        "0.,0.,1.;";
    ParamTokenizer tok(data, ',', ';');
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().N() == 2);
    CHECK(r.value().A() == 4);
    CHECK(r.value().knots.size() == 5);
}

// ─────────────────────────────────────────────────────────────────
// §4.23: "Weight vector length = K+1"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.23 — weight vector length = K+1", "[entity][spec-4.23]") {
    // §4.23: Weights W(0) through W(K) → K+1 values
    ParamTokenizer tok(kCubicBezier, ',', ';');
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().weights.size() == 4);  // K+1 = 3+1
}

// ─────────────────────────────────────────────────────────────────
// §4.23: "Control points vector length = K+1"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.23 — control points vector length = K+1", "[entity][spec-4.23]") {
    // §4.23: Control points X(0),Y(0),Z(0) through X(K),Y(K),Z(K) → K+1
    ParamTokenizer tok(kCubicBezier, ',', ';');
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().control_points.size() == 4);  // K+1
}

// ─────────────────────────────────────────────────────────────────
// §4.23: "The weights shall be positive real numbers"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.23 — all weights are positive", "[entity][spec-4.23]") {
    // §4.23: "The weights shall be positive real numbers"
    ParamTokenizer tok(kCubicBezier, ',', ';');
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());
    for (auto w : r.value().weights) {
        CHECK(w > 0.0);
    }
}

// ─────────────────────────────────────────────────────────────────
// §4.23: "PROP1: planar flag; if 1, plane normal shall be unit vector"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.23 — planar curve: plane normal is unit vector", "[entity][spec-4.23]") {
    // §4.23: "If it is set to 1, the plane normal ... shall contain
    //   a unit vector normal to the plane containing the curve."
    ParamTokenizer tok(kCubicBezier, ',', ';');
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().prop1 == 1);
    Real nlen = r.value().plane_normal.length();
    CHECK_THAT(nlen, WithinRel(1.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.23: "PROP3: polynomial flag; if 1, all weights equal"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.23 — polynomial curve has all weights equal", "[entity][spec-4.23]") {
    // §4.23: "If all weights are equal to each other, the curve is
    //   polynomial and PROP3 shall be set to 1"
    ParamTokenizer tok(kCubicBezier, ',', ';');
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().prop3 == 1);
    auto& w = r.value().weights;
    for (size_t i = 1; i < w.size(); ++i) {
        CHECK(w[i] == w[0]);
    }
}

// ─────────────────────────────────────────────────────────────────
// §4.23: "V(0) and V(1)" — starting and ending parameter values
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.23 — parameter range V(0) to V(1) parsed", "[entity][spec-4.23]") {
    // §4.23: "V(0) = Starting parameter value, V(1) = Ending parameter value"
    ParamTokenizer tok(kCubicBezier, ',', ';');
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r.value().v0, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r.value().v1, WithinRel(1.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.23: "the control points are in the definition space of the curve"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.23 — control points parsed correctly", "[entity][spec-4.23]") {
    // §4.23: "Note that the control points are in the definition space
    //   of the curve"
    ParamTokenizer tok(kCubicBezier, ',', ';');
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());
    auto& pts = r.value().control_points;
    CHECK_THAT(pts[0].x, WithinAbs(0.0, 1e-15));
    CHECK_THAT(pts[0].y, WithinAbs(0.0, 1e-15));
    CHECK_THAT(pts[1].x, WithinRel(1.0));
    CHECK_THAT(pts[1].y, WithinRel(1.0));
    CHECK_THAT(pts[2].x, WithinRel(2.0));
    CHECK_THAT(pts[2].y, WithinRel(1.0));
    CHECK_THAT(pts[3].x, WithinRel(3.0));
    CHECK_THAT(pts[3].y, WithinAbs(0.0, 1e-15));
}

// ─────────────────────────────────────────────────────────────────
// §4.23: Evaluation — Bezier curve at t=0 gives first control point,
//   at t=1 gives last control point
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.23 — evaluate at V(0) gives first control point", "[entity][spec-4.23]") {
    // §4.23: For a Bezier curve, C(0) = P0
    ParamTokenizer tok(kCubicBezier, ',', ';');
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());
    auto p = r.value().evaluate(0.0);
    CHECK_THAT(p.x, WithinAbs(0.0, 1e-10));
    CHECK_THAT(p.y, WithinAbs(0.0, 1e-10));
    CHECK_THAT(p.z, WithinAbs(0.0, 1e-10));
}

TEST_CASE("§4.23 — evaluate at V(1) gives last control point", "[entity][spec-4.23]") {
    // §4.23: For a Bezier curve, C(1) = P_K
    ParamTokenizer tok(kCubicBezier, ',', ';');
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());
    auto p = r.value().evaluate(1.0);
    CHECK_THAT(p.x, WithinRel(3.0));
    CHECK_THAT(p.y, WithinAbs(0.0, 1e-10));
    CHECK_THAT(p.z, WithinAbs(0.0, 1e-10));
}

// ─────────────────────────────────────────────────────────────────
// §4.23: Straight line as degree-1 B-spline (Form 1)
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.23 — degree-1 B-spline represents a line", "[entity][spec-4.23]") {
    // §4.23: Form 1 = "Line"
    //   K=1, M=1 → N=1, A=3 → 4 knots: [0,0,1,1]
    //   Weights: [1,1], Points: (0,0,0),(10,0,0)
    const char* data =
        "1,1,"
        "0,0,1,0,"
        "0.,0.,1.,1.,"
        "1.,1.,"
        "0.,0.,0.,"
        "10.,0.,0.,"
        "0.,1.,"
        "0.,0.,1.;";
    ParamTokenizer tok(data, ',', ';');
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());
    // Midpoint should be (5,0,0)
    auto mid = r.value().evaluate(0.5);
    CHECK_THAT(mid.x, WithinRel(5.0));
    CHECK_THAT(mid.y, WithinAbs(0.0, 1e-10));
}

// ─────────────────────────────────────────────────────────────────
// §4.23: Rational circle arc as weighted B-spline
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.23 — rational quarter circle arc", "[entity][spec-4.23]") {
    // §4.23: A quarter circle can be represented as a rational
    //   quadratic B-spline: K=2, M=2 → N=1, A=5 → 6 knots
    //   Knots: [0,0,0,1,1,1], Weights: [1, 1/sqrt(2), 1]
    //   Points: (1,0,0), (1,1,0), (0,1,0)
    //   This should evaluate at t=0 → (1,0,0), t=1 → (0,1,0)
    const char* data =
        "2,2,"
        "1,0,0,0,"                          // planar, open, rational, nonperiodic
        "0.,0.,0.,1.,1.,1.,"                // 6 knots
        "1.,0.70710678118654752,1.,"         // weights: 1, 1/sqrt(2), 1
        "1.,0.,0.,"                          // P0 = (1,0,0)
        "1.,1.,0.,"                          // P1 = (1,1,0)
        "0.,1.,0.,"                          // P2 = (0,1,0)
        "0.,1.,"                             // V(0)=0, V(1)=1
        "0.,0.,1.;";                         // plane normal
    ParamTokenizer tok(data, ',', ';');
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().prop3 == 0);  // rational (weights differ)

    // At t=0, should be (1,0,0)
    auto p0 = r.value().evaluate(0.0);
    CHECK_THAT(p0.x, WithinAbs(1.0, 1e-10));
    CHECK_THAT(p0.y, WithinAbs(0.0, 1e-10));

    // At t=1, should be (0,1,0)
    auto p1 = r.value().evaluate(1.0);
    CHECK_THAT(p1.x, WithinAbs(0.0, 1e-10));
    CHECK_THAT(p1.y, WithinAbs(1.0, 1e-10));

    // At t=0.5, should be on the unit circle: x^2 + y^2 ≈ 1
    auto pm = r.value().evaluate(0.5);
    Real dist = std::sqrt(pm.x * pm.x + pm.y * pm.y);
    CHECK_THAT(dist, WithinRel(1.0, 1e-6));
}
