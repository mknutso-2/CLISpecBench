// Tests for §4.15 — Parametric Spline Surface Entity (Type 114).
// Spec reference: IGES 5.3, §4.15, pages 98-101.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/parametric_spline_surface_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// Helper: build a single-patch bilinear surface: flat plane in XY from (0,0) to (1,1).
// X(u,v) = u, Y(u,v) = v, Z(u,v) = 0
// With s = u - TU(1), t = v - TV(1), TU = {0,1}, TV = {0,1}:
// X = s (AX=0, BX=1, rest 0); Y = t (AY=0,...,EY=1 where EY is coeff for t^1*s^0)
// Mapping: coeff[4*r+c] for s^c * t^r
// X: coeff_x[1] = 1 (s^1 * t^0), all others 0
// Y: coeff_y[4] = 1 (s^0 * t^1), all others 0
// Z: all zero
static ParametricSplineSurfaceEntity make_flat_patch() {
    ParametricSplineSurfaceEntity e;
    e.ctype = 1;  // Linear
    e.ptype = 1;  // Cartesian product
    e.M = 1;
    e.N = 1;
    e.tu = {0.0, 1.0};
    e.tv = {0.0, 1.0};

    SplineSurfacePatch patch;
    // X = s => coeff_x[1] = 1 (index 4*0+1 = 1)
    patch.coeff_x[1] = 1.0;
    // Y = t => coeff_y[4] = 1 (index 4*1+0 = 4)
    patch.coeff_y[4] = 1.0;
    // Z = 0
    e.patches = {patch};
    return e;
}

// ─────────────────────────────────────────────────────────────────
// §4.15: "CTYPE: Spline Boundary Type, PTYPE: Patch Type,
//   M: u segments, N: v segments"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.15 — parse parametric spline surface header", "[entity][spec-4.15]") {
    // §4.15 PD: "Index 1: CTYPE, 2: PTYPE, 3: M, 4: N"
    auto e = make_flat_patch();
    auto pd = write_parametric_spline_surface_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_parametric_spline_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ctype == 1);
    CHECK(r->ptype == 1);
    CHECK(r->M == 1);
    CHECK(r->N == 1);
    CHECK(r->tu.size() == 2);
    CHECK(r->tv.size() == 2);
    CHECK(r->patches.size() == 1);
}

// ─────────────────────────────────────────────────────────────────
// §4.15: "X(u,v) = sum coefficients * s^c * t^r"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.15 — evaluate flat patch at corners", "[entity][spec-4.15]") {
    // §4.15: Bilinear patch X=u, Y=v, Z=0
    auto e = make_flat_patch();

    auto p00 = e.evaluate(0.0, 0.0);
    CHECK_THAT(p00.x, WithinAbs(0.0, 1e-15));
    CHECK_THAT(p00.y, WithinAbs(0.0, 1e-15));
    CHECK_THAT(p00.z, WithinAbs(0.0, 1e-15));

    auto p10 = e.evaluate(1.0, 0.0);
    CHECK_THAT(p10.x, WithinRel(1.0));
    CHECK_THAT(p10.y, WithinAbs(0.0, 1e-15));

    auto p01 = e.evaluate(0.0, 1.0);
    CHECK_THAT(p01.x, WithinAbs(0.0, 1e-15));
    CHECK_THAT(p01.y, WithinRel(1.0));

    auto p11 = e.evaluate(1.0, 1.0);
    CHECK_THAT(p11.x, WithinRel(1.0));
    CHECK_THAT(p11.y, WithinRel(1.0));
}

TEST_CASE("§4.15 — evaluate flat patch at midpoint", "[entity][spec-4.15]") {
    // §4.15: At (0.5, 0.5): X=0.5, Y=0.5, Z=0
    auto e = make_flat_patch();
    auto p = e.evaluate(0.5, 0.5);
    CHECK_THAT(p.x, WithinRel(0.5));
    CHECK_THAT(p.y, WithinRel(0.5));
    CHECK_THAT(p.z, WithinAbs(0.0, 1e-15));
}

// ─────────────────────────────────────────────────────────────────
// §4.15: "PTYPE: Patch Type: 0=Unspecified, 1=Cartesian Product"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.15 — patch type preserved in round-trip", "[entity][spec-4.15]") {
    // §4.15: "PTYPE 1 = Cartesian Product"
    auto e = make_flat_patch();
    e.ptype = 0;  // Unspecified
    auto pd = write_parametric_spline_surface_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_parametric_spline_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ptype == 0);
}

// ─────────────────────────────────────────────────────────────────
// §4.15: Quadratic Z height patch
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.15 — quadratic height patch", "[entity][spec-4.15]") {
    // §4.15: Z(u,v) = s^2 (paraboloid cross-section)
    // coeff_z[2] = 1 (s^2 * t^0)
    ParametricSplineSurfaceEntity e;
    e.ctype = 2; e.ptype = 1; e.M = 1; e.N = 1;
    e.tu = {0.0, 1.0}; e.tv = {0.0, 1.0};
    SplineSurfacePatch patch;
    patch.coeff_x[1] = 1.0;  // X = s
    patch.coeff_y[4] = 1.0;  // Y = t
    patch.coeff_z[2] = 1.0;  // Z = s^2
    e.patches = {patch};

    auto p = e.evaluate(0.5, 0.5);
    CHECK_THAT(p.z, WithinRel(0.25));  // 0.5^2

    auto p2 = e.evaluate(1.0, 0.0);
    CHECK_THAT(p2.z, WithinRel(1.0));  // 1.0^2
}

// ─────────────────────────────────────────────────────────────────
// Round-trip: write then parse
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.15 — round-trip parametric spline surface", "[entity][spec-4.15]") {
    auto orig = make_flat_patch();
    auto pd = write_parametric_spline_surface_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_parametric_spline_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ctype == orig.ctype);
    CHECK(r->ptype == orig.ptype);
    CHECK(r->M == orig.M);
    CHECK(r->N == orig.N);
    CHECK(r->patches.size() == 1);
    CHECK_THAT(r->patches[0].coeff_x[1], WithinRel(1.0));
    CHECK_THAT(r->patches[0].coeff_y[4], WithinRel(1.0));
}
