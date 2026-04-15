// Tests for §4.14 — Parametric Spline Curve Entity (Type 112).
// Spec reference: IGES 5.3, §4.14, pages 94-97.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/parametric_spline_curve_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"
#include <cmath>

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// Helper: build a linear spline curve from (0,0,0) to (3,0,0) with 1 segment.
// X(u) = A + B*s, s = u - T(1). T(1)=0, T(2)=3.
// AX=0, BX=1, CX=0, DX=0, AY=0,..., AZ=0,...
static ParametricSplineCurveEntity make_linear_spline() {
    ParametricSplineCurveEntity e;
    e.ctype = 1;  // Linear
    e.H = 0;
    e.ndim = 3;
    e.breakpoints = {0.0, 3.0};
    SplineCurveSegment seg;
    seg.ax = 0.0; seg.bx = 1.0; seg.cx = 0.0; seg.dx = 0.0;
    seg.ay = 0.0; seg.by = 0.0; seg.cy = 0.0; seg.dy = 0.0;
    seg.az = 0.0; seg.bz = 0.0; seg.cz = 0.0; seg.dz = 0.0;
    e.segments = {seg};
    // Terminate point: at u=3, s=3: X=3, Y=0, Z=0
    e.tpx0 = 3.0; e.tpx1 = 1.0; e.tpx2 = 0.0; e.tpx3 = 0.0;
    e.tpy0 = 0.0; e.tpy1 = 0.0; e.tpy2 = 0.0; e.tpy3 = 0.0;
    e.tpz0 = 0.0; e.tpz1 = 0.0; e.tpz2 = 0.0; e.tpz3 = 0.0;
    return e;
}

// ─────────────────────────────────────────────────────────────────
// §4.14: "CTYPE: Spline Type: 1=Linear, 2=Quadratic, 3=Cubic"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.14 — parse parametric spline curve header", "[entity][spec-4.14]") {
    // §4.14 PD: "Index 1: CTYPE, 2: H, 3: NDIM, 4: N"
    auto e = make_linear_spline();
    auto pd = write_parametric_spline_curve_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_parametric_spline_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ctype == 1);
    CHECK(r->H == 0);
    CHECK(r->ndim == 3);
    CHECK(r->segments.size() == 1);
    CHECK(r->breakpoints.size() == 2);
}

// ─────────────────────────────────────────────────────────────────
// §4.14: "X(u) = AX(i) + s*BX(i) + s^2*CX(i) + s^3*DX(i)"
//   "where T(i) <= u <= T(i+1), s = u - T(i)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.14 — evaluate linear spline at breakpoints", "[entity][spec-4.14]") {
    // §4.14: "X(u) = AX + s*BX" (linear: CX=DX=0)
    auto e = make_linear_spline();

    auto p0 = e.evaluate(0.0);
    CHECK_THAT(p0.x, WithinAbs(0.0, 1e-15));
    CHECK_THAT(p0.y, WithinAbs(0.0, 1e-15));
    CHECK_THAT(p0.z, WithinAbs(0.0, 1e-15));

    auto p3 = e.evaluate(3.0);
    CHECK_THAT(p3.x, WithinRel(3.0));
    CHECK_THAT(p3.y, WithinAbs(0.0, 1e-15));
}

TEST_CASE("§4.14 — evaluate linear spline at midpoint", "[entity][spec-4.14]") {
    // §4.14: At u=1.5, s=1.5: X(1.5) = 0 + 1*1.5 = 1.5
    auto e = make_linear_spline();
    auto p = e.evaluate(1.5);
    CHECK_THAT(p.x, WithinRel(1.5));
}

// ─────────────────────────────────────────────────────────────────
// §4.14: Multi-segment cubic spline
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.14 — multi-segment cubic spline evaluate", "[entity][spec-4.14]") {
    // §4.14: Two cubic segments.
    // Segment 1: T(1)=0, T(2)=1. X(u) = u^3 (AX=0,BX=0,CX=0,DX=1)
    // Segment 2: T(2)=1, T(3)=2. X(u) = 1 + 3*s + 3*s^2 + s^3 (continues x^3)
    ParametricSplineCurveEntity e;
    e.ctype = 3;
    e.H = 2;
    e.ndim = 3;
    e.breakpoints = {0.0, 1.0, 2.0};

    SplineCurveSegment seg1;
    seg1.ax = 0.0; seg1.bx = 0.0; seg1.cx = 0.0; seg1.dx = 1.0;
    seg1.ay = 0.0; seg1.by = 0.0; seg1.cy = 0.0; seg1.dy = 0.0;
    seg1.az = 0.0; seg1.bz = 0.0; seg1.cz = 0.0; seg1.dz = 0.0;

    SplineCurveSegment seg2;
    seg2.ax = 1.0; seg2.bx = 3.0; seg2.cx = 3.0; seg2.dx = 1.0;
    seg2.ay = 0.0; seg2.by = 0.0; seg2.cy = 0.0; seg2.dy = 0.0;
    seg2.az = 0.0; seg2.bz = 0.0; seg2.cz = 0.0; seg2.dz = 0.0;

    e.segments = {seg1, seg2};
    e.tpx0 = 8.0; e.tpx1 = 12.0; e.tpx2 = 6.0; e.tpx3 = 1.0;
    e.tpy0 = 0.0; e.tpy1 = 0.0; e.tpy2 = 0.0; e.tpy3 = 0.0;
    e.tpz0 = 0.0; e.tpz1 = 0.0; e.tpz2 = 0.0; e.tpz3 = 0.0;

    // At u=0: X = 0^3 = 0
    CHECK_THAT(e.evaluate(0.0).x, WithinAbs(0.0, 1e-12));
    // At u=0.5: X = 0.5^3 = 0.125
    CHECK_THAT(e.evaluate(0.5).x, WithinRel(0.125, 1e-12));
    // At u=1.0: X = 1^3 = 1 (start of segment 2, s=0)
    CHECK_THAT(e.evaluate(1.0).x, WithinRel(1.0, 1e-12));
    // At u=2.0: s=1, X = 1 + 3 + 3 + 1 = 8 = 2^3
    CHECK_THAT(e.evaluate(2.0).x, WithinRel(8.0, 1e-12));
}

// ─────────────────────────────────────────────────────────────────
// §4.14: "If the spline is planar, NDIM=2"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.14 — planar spline has NDIM=2", "[entity][spec-4.14]") {
    // §4.14: "NDIM: 2=planar, 3=nonplanar"
    auto e = make_linear_spline();
    e.ndim = 2;
    auto pd = write_parametric_spline_curve_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_parametric_spline_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ndim == 2);
}

// ─────────────────────────────────────────────────────────────────
// Round-trip: write then parse
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.14 — round-trip parametric spline curve", "[entity][spec-4.14]") {
    auto orig = make_linear_spline();
    auto pd = write_parametric_spline_curve_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_parametric_spline_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ctype == orig.ctype);
    CHECK(r->H == orig.H);
    CHECK(r->ndim == orig.ndim);
    CHECK(r->breakpoints.size() == orig.breakpoints.size());
    CHECK(r->segments.size() == orig.segments.size());
    CHECK_THAT(r->segments[0].bx, WithinRel(1.0));
    CHECK_THAT(r->tpx0, WithinRel(3.0));
}
