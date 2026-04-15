// Geometric evaluation tests: create primitive shapes, round-trip through
// IGES file I/O, evaluate surfaces/curves at various points, and confirm
// that the evaluated positions are within tolerance.
//
// These tests verify the full pipeline: entity construction -> serialization
// -> file assembly -> file parsing -> entity parsing -> geometric evaluation.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "writer/file_writer.hpp"
#include "writer/entity_writer.hpp"
#include "parser/file_reader.hpp"
#include "parser/param_tokenizer.hpp"
#include "entities/line_entity.hpp"
#include "entities/circular_arc_entity.hpp"
#include "entities/rational_bspline_curve_entity.hpp"
#include "entities/rational_bspline_surface_entity.hpp"
#include "entities/transformation_matrix_entity.hpp"
#include "entities/block_entity.hpp"
#include "entities/sphere_entity.hpp"
#include "entities/right_circular_cylinder_entity.hpp"
#include "entities/cone_frustum_entity.hpp"
#include "entities/torus_entity.hpp"
#include <sstream>
#include <cmath>
#include <numbers>

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

static constexpr Real kTol = 1e-10;
static constexpr Real kPi = std::numbers::pi;

static GlobalSection make_test_global() {
    GlobalSection g;
    g.product_id_sender = "GEOM-EVAL";
    g.file_name = "geom_eval.igs";
    g.native_system_id = "IGES-SDK";
    g.preprocessor_version = "1.0";
    g.integer_bits = 32;
    g.sp_magnitude = 38;
    g.sp_significance = 6;
    g.dp_magnitude = 308;
    g.dp_significance = 15;
    g.units = Units::Millimeters;
    g.units_name = "MM";
    return g;
}

// Helper: round-trip an IGES file through write + read
static IgesFile round_trip(std::vector<WritableEntity> const& entities) {
    auto file_str = write_iges_file({"Geometric eval test"}, make_test_global(), entities);
    std::istringstream iss(file_str);
    auto result = read_iges_file(iss);
    REQUIRE(result.has_value());
    return std::move(result.value());
}

// ── Helper: build a quarter-circle B-spline curve ─────────────────
// Rational quadratic Bezier: K=2, M=2
// Traces from (R, 0, 0) to (0, R, 0) along a quarter-circle
static RationalBSplineCurveEntity make_quarter_circle(Real R) {
    RationalBSplineCurveEntity c;
    c.K = 2;
    c.M = 2;
    c.prop1 = 1;  // planar
    c.prop2 = 0;  // open
    c.prop3 = 0;  // rational
    c.prop4 = 0;  // nonperiodic
    c.knots = {0, 0, 0, 1, 1, 1};
    c.weights = {1.0, 1.0 / std::sqrt(2.0), 1.0};
    c.control_points = {{R, 0, 0}, {R, R, 0}, {0, R, 0}};
    c.v0 = 0.0;
    c.v1 = 1.0;
    c.plane_normal = {0, 0, 1};
    return c;
}

// ── Helper: build a degree-1 B-spline curve (straight line) ──────
// K=1, M=1: two control points = line segment from P0 to P1
static RationalBSplineCurveEntity make_bspline_line(Vec3 p0, Vec3 p1) {
    RationalBSplineCurveEntity c;
    c.K = 1;
    c.M = 1;
    c.prop1 = 0;
    c.prop2 = 0;
    c.prop3 = 1;  // polynomial
    c.prop4 = 0;
    c.knots = {0, 0, 1, 1};
    c.weights = {1.0, 1.0};
    c.control_points = {p0, p1};
    c.v0 = 0.0;
    c.v1 = 1.0;
    return c;
}

// ── Helper: build a flat bilinear B-spline surface patch ─────────
// Corners at (0,0,Z), (W,0,Z), (0,H,Z), (W,H,Z)
static RationalBSplineSurfaceEntity make_flat_plane(Real W, Real H, Real Z) {
    RationalBSplineSurfaceEntity s;
    s.K1 = 1; s.K2 = 1;
    s.M1 = 1; s.M2 = 1;
    s.prop1 = 0; s.prop2 = 0;
    s.prop3 = 1;  // polynomial
    s.prop4 = 0; s.prop5 = 0;
    s.knots_u = {0, 0, 1, 1};
    s.knots_v = {0, 0, 1, 1};
    // Control points stored u-major: (0,0), (1,0), (0,1), (1,1)
    s.control_points = {{0, 0, Z}, {W, 0, Z}, {0, H, Z}, {W, H, Z}};
    s.weights = {1, 1, 1, 1};
    s.u0 = 0; s.u1 = 1;
    s.v0 = 0; s.v1 = 1;
    return s;
}

// ── Helper: build a cylindrical surface patch ────────────────────
// Quarter-cylinder of radius R, height H, along the Z-axis.
// u direction: quarter-circle (rational quadratic)
// v direction: linear from z=0 to z=H
static RationalBSplineSurfaceEntity make_quarter_cylinder(Real R, Real H) {
    RationalBSplineSurfaceEntity s;
    s.K1 = 2; s.K2 = 1;  // 3 in u, 2 in v
    s.M1 = 2; s.M2 = 1;  // quadratic in u, linear in v
    s.prop1 = 0; s.prop2 = 0;
    s.prop3 = 0;  // rational (weights differ)
    s.prop4 = 0; s.prop5 = 0;
    s.knots_u = {0, 0, 0, 1, 1, 1};
    s.knots_v = {0, 0, 1, 1};

    Real w = 1.0 / std::sqrt(2.0);

    // Storage: u-index varies fastest, v-row 0 then v-row 1
    // Row v=0 (z=0): quarter circle at base
    // Row v=1 (z=H): quarter circle at top
    s.control_points = {
        {R, 0, 0}, {R, R, 0}, {0, R, 0},   // v=0
        {R, 0, H}, {R, R, H}, {0, R, H},    // v=1
    };
    s.weights = {1, w, 1, 1, w, 1};
    s.u0 = 0; s.u1 = 1;
    s.v0 = 0; s.v1 = 1;
    return s;
}

// =================================================================
// Line evaluation with round-trip
// =================================================================

TEST_CASE("Geometric eval -- line round-trip evaluation at multiple t values",
          "[geometric][eval]") {
    LineEntity le;
    le.start = {10, 20, 30};
    le.terminate = {40, 50, 60};

    DirectoryEntry de;
    de.entity_type = EntityType{110};

    auto file = round_trip({{de, write_line_entity(le)}});
    REQUIRE(file.entities.size() == 1);

    ParamTokenizer tok(file.entities[0].pd_string,
                       file.global.param_delimiter,
                       file.global.record_delimiter);
    auto r = parse_line_entity(tok);
    REQUIRE(r.has_value());

    // Evaluate at t = 0, 0.25, 0.5, 0.75, 1
    for (Real t : {0.0, 0.25, 0.5, 0.75, 1.0}) {
        auto p = r->evaluate(t);
        Real expected_x = 10.0 + t * 30.0;
        Real expected_y = 20.0 + t * 30.0;
        Real expected_z = 30.0 + t * 30.0;
        CHECK_THAT(p.x, WithinAbs(expected_x, kTol));
        CHECK_THAT(p.y, WithinAbs(expected_y, kTol));
        CHECK_THAT(p.z, WithinAbs(expected_z, kTol));
    }
}

// =================================================================
// Circular arc evaluation with round-trip
// =================================================================

TEST_CASE("Geometric eval -- circular arc round-trip, all points on circle",
          "[geometric][eval]") {
    // Quarter circle: center (5,5), radius 10, from (15,5) to (5,15)
    CircularArcEntity ca;
    ca.zt = 3.0;
    ca.x1 = 5.0; ca.y1 = 5.0;   // center
    ca.x2 = 15.0; ca.y2 = 5.0;  // start (R=10, angle=0)
    ca.x3 = 5.0; ca.y3 = 15.0;  // terminate (angle=pi/2)

    DirectoryEntry de;
    de.entity_type = EntityType{100};

    auto file = round_trip({{de, write_circular_arc_entity(ca)}});
    REQUIRE(file.entities.size() == 1);

    ParamTokenizer tok(file.entities[0].pd_string,
                       file.global.param_delimiter,
                       file.global.record_delimiter);
    auto r = parse_circular_arc_entity(tok);
    REQUIRE(r.has_value());

    Real R = r->radius();
    CHECK_THAT(R, WithinRel(10.0));

    // Evaluate at 20 equally-spaced angles between start and terminate
    Real a0 = r->start_angle();
    Real a1 = r->terminate_angle();
    for (int i = 0; i <= 20; ++i) {
        Real t = a0 + (a1 - a0) * i / 20.0;
        auto p = r->evaluate(t);

        // Distance from center should equal radius
        Real dx = p.x - r->x1;
        Real dy = p.y - r->y1;
        Real dist = std::sqrt(dx * dx + dy * dy);
        CHECK_THAT(dist, WithinRel(10.0, 1e-12));

        // Z should be ZT
        CHECK_THAT(p.z, WithinRel(3.0));
    }
}

// =================================================================
// B-spline curve: degree-1 line segment
// =================================================================

TEST_CASE("Geometric eval -- B-spline degree-1 curve is a straight line",
          "[geometric][eval]") {
    auto c = make_bspline_line({0, 0, 0}, {12, 6, 3});

    DirectoryEntry de;
    de.entity_type = EntityType{126};

    auto file = round_trip({{de, write_rational_bspline_curve_entity(c)}});
    REQUIRE(file.entities.size() == 1);

    ParamTokenizer tok(file.entities[0].pd_string,
                       file.global.param_delimiter,
                       file.global.record_delimiter);
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());

    for (int i = 0; i <= 10; ++i) {
        Real t = i / 10.0;
        auto p = r->evaluate(t);

        // Should match linear interpolation
        CHECK_THAT(p.x, WithinAbs(12.0 * t, kTol));
        CHECK_THAT(p.y, WithinAbs(6.0 * t, kTol));
        CHECK_THAT(p.z, WithinAbs(3.0 * t, kTol));
    }
}

// =================================================================
// B-spline curve: quarter circle, all points at constant radius
// =================================================================

TEST_CASE("Geometric eval -- rational B-spline quarter circle, constant radius",
          "[geometric][eval]") {
    Real R = 25.0;
    auto c = make_quarter_circle(R);

    DirectoryEntry de;
    de.entity_type = EntityType{126};

    auto file = round_trip({{de, write_rational_bspline_curve_entity(c)}});
    REQUIRE(file.entities.size() == 1);

    ParamTokenizer tok(file.entities[0].pd_string,
                       file.global.param_delimiter,
                       file.global.record_delimiter);
    auto r = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r.has_value());

    // Evaluate at 50 parameter values
    for (int i = 0; i <= 50; ++i) {
        Real t = i / 50.0;
        auto p = r->evaluate(t);

        // Every point should be at distance R from origin
        Real dist = std::sqrt(p.x * p.x + p.y * p.y);
        CHECK_THAT(dist, WithinRel(R, 1e-8));

        // Z should be 0
        CHECK_THAT(p.z, WithinAbs(0.0, kTol));

        // All points should be in the first quadrant
        CHECK(p.x >= -kTol);
        CHECK(p.y >= -kTol);
    }

    // Endpoint checks
    auto p0 = r->evaluate(0.0);
    CHECK_THAT(p0.x, WithinAbs(R, kTol));
    CHECK_THAT(p0.y, WithinAbs(0.0, kTol));

    auto p1 = r->evaluate(1.0);
    CHECK_THAT(p1.x, WithinAbs(0.0, kTol));
    CHECK_THAT(p1.y, WithinAbs(R, kTol));
}

// =================================================================
// B-spline surface: flat plane, all points at constant Z
// =================================================================

TEST_CASE("Geometric eval -- bilinear surface is flat plane at Z=5",
          "[geometric][eval]") {
    Real W = 100.0, H = 50.0, Z = 5.0;
    auto s = make_flat_plane(W, H, Z);

    DirectoryEntry de;
    de.entity_type = EntityType{128};

    auto file = round_trip({{de, write_rational_bspline_surface_entity(s)}});
    REQUIRE(file.entities.size() == 1);

    ParamTokenizer tok(file.entities[0].pd_string,
                       file.global.param_delimiter,
                       file.global.record_delimiter);
    auto r = parse_rational_bspline_surface_entity(tok);
    REQUIRE(r.has_value());

    // Evaluate at a 10x10 grid of (u,v) values
    for (int i = 0; i <= 10; ++i) {
        for (int j = 0; j <= 10; ++j) {
            Real u = i / 10.0;
            Real v = j / 10.0;
            auto p = r->evaluate(u, v);

            // X should interpolate linearly: u * W
            CHECK_THAT(p.x, WithinAbs(u * W, kTol));

            // Y should interpolate linearly: v * H
            CHECK_THAT(p.y, WithinAbs(v * H, kTol));

            // Z should be constant at Z
            CHECK_THAT(p.z, WithinAbs(Z, kTol));
        }
    }
}

// =================================================================
// B-spline surface: quarter-cylinder, constant radius from axis
// =================================================================

TEST_CASE("Geometric eval -- quarter-cylinder surface, constant radius",
          "[geometric][eval]") {
    Real R = 10.0, H = 30.0;
    auto s = make_quarter_cylinder(R, H);

    DirectoryEntry de;
    de.entity_type = EntityType{128};

    auto file = round_trip({{de, write_rational_bspline_surface_entity(s)}});
    REQUIRE(file.entities.size() == 1);

    ParamTokenizer tok(file.entities[0].pd_string,
                       file.global.param_delimiter,
                       file.global.record_delimiter);
    auto r = parse_rational_bspline_surface_entity(tok);
    REQUIRE(r.has_value());

    // Evaluate at a 20x10 grid
    for (int i = 0; i <= 20; ++i) {
        for (int j = 0; j <= 10; ++j) {
            Real u = i / 20.0;
            Real v = j / 10.0;
            auto p = r->evaluate(u, v);

            // Distance from the Z-axis should equal R
            Real dist_from_axis = std::sqrt(p.x * p.x + p.y * p.y);
            CHECK_THAT(dist_from_axis, WithinRel(R, 1e-8));

            // Z should interpolate linearly: v * H
            CHECK_THAT(p.z, WithinAbs(v * H, 1e-8));

            // Points should be in the first quadrant (quarter cylinder)
            CHECK(p.x >= -1e-8);
            CHECK(p.y >= -1e-8);
        }
    }
}

// =================================================================
// Transformation matrix: rotation + translation
// =================================================================

TEST_CASE("Geometric eval -- transformation matrix applies correctly",
          "[geometric][eval]") {
    // 90-degree rotation about Z-axis + translation (10, 20, 30)
    TransformationMatrixEntity xform;
    xform.rotation(0, 0) =  0; xform.rotation(0, 1) = -1; xform.rotation(0, 2) = 0;
    xform.rotation(1, 0) =  1; xform.rotation(1, 1) =  0; xform.rotation(1, 2) = 0;
    xform.rotation(2, 0) =  0; xform.rotation(2, 1) =  0; xform.rotation(2, 2) = 1;
    xform.translation = {10, 20, 30};

    DirectoryEntry de;
    de.entity_type = EntityType{124};

    auto file = round_trip({{de, write_transformation_matrix_entity(xform)}});
    REQUIRE(file.entities.size() == 1);

    ParamTokenizer tok(file.entities[0].pd_string,
                       file.global.param_delimiter,
                       file.global.record_delimiter);
    auto r = parse_transformation_matrix_entity(tok);
    REQUIRE(r.has_value());

    // Apply to (1, 0, 0): should become (0+10, 1+20, 0+30) = (10, 21, 30)
    auto p1 = r->apply({1, 0, 0});
    CHECK_THAT(p1.x, WithinAbs(10.0, kTol));
    CHECK_THAT(p1.y, WithinAbs(21.0, kTol));
    CHECK_THAT(p1.z, WithinAbs(30.0, kTol));

    // Apply to (0, 1, 0): should become (-1+10, 0+20, 0+30) = (9, 20, 30)
    auto p2 = r->apply({0, 1, 0});
    CHECK_THAT(p2.x, WithinAbs(9.0, kTol));
    CHECK_THAT(p2.y, WithinAbs(20.0, kTol));
    CHECK_THAT(p2.z, WithinAbs(30.0, kTol));

    // Apply to (0, 0, 5): should become (0+10, 0+20, 5+30) = (10, 20, 35)
    auto p3 = r->apply({0, 0, 5});
    CHECK_THAT(p3.x, WithinAbs(10.0, kTol));
    CHECK_THAT(p3.y, WithinAbs(20.0, kTol));
    CHECK_THAT(p3.z, WithinAbs(35.0, kTol));
}

TEST_CASE("Geometric eval -- transformation matrix composition",
          "[geometric][eval]") {
    // Two transforms: T1 = translate by (5,0,0), T2 = translate by (0,10,0)
    TransformationMatrixEntity t1;
    t1.translation = {5, 0, 0};

    TransformationMatrixEntity t2;
    t2.translation = {0, 10, 0};

    // Compose: t1 after t2 → translate by (5, 10, 0)
    auto composed = t1.compose(t2);
    auto p = composed.apply({0, 0, 0});
    CHECK_THAT(p.x, WithinAbs(5.0, kTol));
    CHECK_THAT(p.y, WithinAbs(10.0, kTol));
    CHECK_THAT(p.z, WithinAbs(0.0, kTol));
}

// =================================================================
// CSG primitives: round-trip and verify dimensions preserved
// =================================================================

TEST_CASE("Geometric eval -- block entity round-trip preserves dimensions",
          "[geometric][eval]") {
    BlockEntity blk;
    blk.lx = 100.0; blk.ly = 50.0; blk.lz = 25.0;
    blk.corner = {10, 20, 30};
    blk.x_axis = {1, 0, 0};
    blk.z_axis = {0, 0, 1};

    DirectoryEntry de;
    de.entity_type = EntityType{150};

    auto file = round_trip({{de, write_block_entity(blk)}});
    REQUIRE(file.entities.size() == 1);
    CHECK(file.entities[0].de.entity_type.value == 150);

    ParamTokenizer tok(file.entities[0].pd_string,
                       file.global.param_delimiter,
                       file.global.record_delimiter);
    auto r = parse_block_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->lx, WithinRel(100.0));
    CHECK_THAT(r->ly, WithinRel(50.0));
    CHECK_THAT(r->lz, WithinRel(25.0));
    CHECK_THAT(r->corner.x, WithinRel(10.0));
    CHECK_THAT(r->corner.y, WithinRel(20.0));
    CHECK_THAT(r->corner.z, WithinRel(30.0));
}

TEST_CASE("Geometric eval -- sphere entity round-trip preserves dimensions",
          "[geometric][eval]") {
    SphereEntity sph;
    sph.radius = 42.5;
    sph.center = {100, 200, 300};

    DirectoryEntry de;
    de.entity_type = EntityType{158};

    auto file = round_trip({{de, write_sphere_entity(sph)}});
    REQUIRE(file.entities.size() == 1);
    CHECK(file.entities[0].de.entity_type.value == 158);

    ParamTokenizer tok(file.entities[0].pd_string,
                       file.global.param_delimiter,
                       file.global.record_delimiter);
    auto r = parse_sphere_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->radius, WithinRel(42.5));
    CHECK_THAT(r->center.x, WithinRel(100.0));
    CHECK_THAT(r->center.y, WithinRel(200.0));
    CHECK_THAT(r->center.z, WithinRel(300.0));
}

TEST_CASE("Geometric eval -- cylinder entity round-trip preserves dimensions",
          "[geometric][eval]") {
    RightCircularCylinderEntity cyl;
    cyl.h = 75.0;
    cyl.r = 15.0;
    cyl.face_center = {0, 0, -37.5};
    cyl.axis = {0, 0, 1};

    DirectoryEntry de;
    de.entity_type = EntityType{154};

    auto file = round_trip({{de, write_right_circular_cylinder_entity(cyl)}});
    REQUIRE(file.entities.size() == 1);
    CHECK(file.entities[0].de.entity_type.value == 154);

    ParamTokenizer tok(file.entities[0].pd_string,
                       file.global.param_delimiter,
                       file.global.record_delimiter);
    auto r = parse_right_circular_cylinder_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->h, WithinRel(75.0));
    CHECK_THAT(r->r, WithinRel(15.0));
    CHECK_THAT(r->face_center.z, WithinRel(-37.5));
    CHECK_THAT(r->axis.z, WithinRel(1.0));
}

TEST_CASE("Geometric eval -- cone frustum entity round-trip",
          "[geometric][eval]") {
    ConeFrustumEntity cone;
    cone.h = 50.0;
    cone.r1 = 20.0;
    cone.r2 = 5.0;
    cone.face_center = {0, 0, 0};
    cone.axis = {0, 0, 1};

    DirectoryEntry de;
    de.entity_type = EntityType{156};

    auto file = round_trip({{de, write_cone_frustum_entity(cone)}});
    REQUIRE(file.entities.size() == 1);

    ParamTokenizer tok(file.entities[0].pd_string,
                       file.global.param_delimiter,
                       file.global.record_delimiter);
    auto r = parse_cone_frustum_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->h, WithinRel(50.0));
    CHECK_THAT(r->r1, WithinRel(20.0));
    CHECK_THAT(r->r2, WithinRel(5.0));
}

TEST_CASE("Geometric eval -- torus entity round-trip preserves dimensions",
          "[geometric][eval]") {
    TorusEntity tor;
    tor.r1 = 50.0;   // major radius
    tor.r2 = 10.0;   // minor radius
    tor.center = {0, 0, 0};
    tor.axis = {0, 0, 1};

    DirectoryEntry de;
    de.entity_type = EntityType{160};

    auto file = round_trip({{de, write_torus_entity(tor)}});
    REQUIRE(file.entities.size() == 1);

    ParamTokenizer tok(file.entities[0].pd_string,
                       file.global.param_delimiter,
                       file.global.record_delimiter);
    auto r = parse_torus_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->r1, WithinRel(50.0));
    CHECK_THAT(r->r2, WithinRel(10.0));
}

// =================================================================
// Combined: multi-entity file with evaluation
// =================================================================

TEST_CASE("Geometric eval -- multi-entity file with mixed geometry",
          "[geometric][eval]") {
    // Build a file with: line + arc + B-spline curve + B-spline surface
    LineEntity le;
    le.start = {0, 0, 0};
    le.terminate = {100, 0, 0};

    CircularArcEntity ca;
    ca.zt = 0;
    ca.x1 = 50; ca.y1 = 0;
    ca.x2 = 75; ca.y2 = 0;
    ca.x3 = 25; ca.y3 = 0;

    auto bsc = make_quarter_circle(30.0);
    auto bss = make_flat_plane(200, 100, 0);

    DirectoryEntry de_line;     de_line.entity_type = EntityType{110};
    DirectoryEntry de_arc;      de_arc.entity_type  = EntityType{100};
    DirectoryEntry de_curve;    de_curve.entity_type = EntityType{126};
    DirectoryEntry de_surf;     de_surf.entity_type  = EntityType{128};

    auto file = round_trip({
        {de_line,  write_line_entity(le)},
        {de_arc,   write_circular_arc_entity(ca)},
        {de_curve, write_rational_bspline_curve_entity(bsc)},
        {de_surf,  write_rational_bspline_surface_entity(bss)},
    });
    REQUIRE(file.entities.size() == 4);

    // Evaluate line at midpoint
    {
        ParamTokenizer tok(file.entities[0].pd_string, ',', ';');
        auto r = parse_line_entity(tok);
        REQUIRE(r.has_value());
        auto mid = r->evaluate(0.5);
        CHECK_THAT(mid.x, WithinAbs(50.0, kTol));
    }

    // Evaluate arc: all points at distance R from center
    {
        ParamTokenizer tok(file.entities[1].pd_string, ',', ';');
        auto r = parse_circular_arc_entity(tok);
        REQUIRE(r.has_value());
        Real R = r->radius();
        CHECK_THAT(R, WithinRel(25.0));

        auto p = r->evaluate(r->start_angle());
        Real dist = std::sqrt((p.x - 50) * (p.x - 50) + p.y * p.y);
        CHECK_THAT(dist, WithinRel(25.0, 1e-12));
    }

    // Evaluate B-spline curve at t=0.5: should be on circle of radius 30
    {
        ParamTokenizer tok(file.entities[2].pd_string, ',', ';');
        auto r = parse_rational_bspline_curve_entity(tok);
        REQUIRE(r.has_value());
        auto p = r->evaluate(0.5);
        Real dist = std::sqrt(p.x * p.x + p.y * p.y);
        CHECK_THAT(dist, WithinRel(30.0, 1e-8));
    }

    // Evaluate surface at center: should be (100, 50, 0)
    {
        ParamTokenizer tok(file.entities[3].pd_string, ',', ';');
        auto r = parse_rational_bspline_surface_entity(tok);
        REQUIRE(r.has_value());
        auto p = r->evaluate(0.5, 0.5);
        CHECK_THAT(p.x, WithinAbs(100.0, kTol));
        CHECK_THAT(p.y, WithinAbs(50.0, kTol));
        CHECK_THAT(p.z, WithinAbs(0.0, kTol));
    }
}

// =================================================================
// Stress: evaluate B-spline surface at many points
// =================================================================

TEST_CASE("Geometric eval -- dense grid evaluation on cylinder patch",
          "[geometric][eval]") {
    Real R = 7.5, H = 20.0;
    auto s = make_quarter_cylinder(R, H);

    // Evaluate at 100x100 = 10000 points (no round-trip, direct eval)
    for (int i = 0; i <= 100; ++i) {
        for (int j = 0; j <= 100; ++j) {
            Real u = i / 100.0;
            Real v = j / 100.0;
            auto p = s.evaluate(u, v);

            Real dist = std::sqrt(p.x * p.x + p.y * p.y);
            REQUIRE_THAT(dist, WithinRel(R, 1e-6));
            REQUIRE_THAT(p.z, WithinAbs(v * H, 1e-6));
        }
    }
}
