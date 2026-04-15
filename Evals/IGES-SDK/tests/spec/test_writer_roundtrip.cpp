// Round-trip tests: parse -> serialize -> re-parse -> compare.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/line_entity.hpp"
#include "entities/circular_arc_entity.hpp"
#include "entities/point_entity.hpp"
#include "entities/composite_curve_entity.hpp"
#include "entities/null_entity.hpp"
#include "entities/transformation_matrix_entity.hpp"
#include "entities/rational_bspline_curve_entity.hpp"
#include "entities/trimmed_surface_entity.hpp"
#include "entities/curve_on_surface_entity.hpp"
#include "entities/ruled_surface_entity.hpp"
#include "entities/surface_of_revolution_entity.hpp"
#include "entities/tabulated_cylinder_entity.hpp"
#include "entities/offset_surface_entity.hpp"
#include "entities/bounded_surface_entity.hpp"
#include "writer/entity_writer.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// ─────────────────────────────────────────────────────────────────
// RT-1: Line entity round-trip
// ─────────────────────────────────────────────────────────────────

TEST_CASE("RT-1 — line entity round-trip", "[writer][round-trip]") {
    // Parse
    ParamTokenizer tok("1.5,2.5,3.5,4.5,5.5,6.5;", ',', ';');
    auto r1 = parse_line_entity(tok);
    REQUIRE(r1.has_value());

    // Serialize
    std::string s = write_line_entity(r1.value());

    // Re-parse
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_line_entity(tok2);
    REQUIRE(r2.has_value());

    // Compare
    CHECK_THAT(r2->start.x, WithinRel(1.5));
    CHECK_THAT(r2->start.y, WithinRel(2.5));
    CHECK_THAT(r2->start.z, WithinRel(3.5));
    CHECK_THAT(r2->terminate.x, WithinRel(4.5));
    CHECK_THAT(r2->terminate.y, WithinRel(5.5));
    CHECK_THAT(r2->terminate.z, WithinRel(6.5));
}

// ─────────────────────────────────────────────────────────────────
// RT-2: Circular arc entity round-trip
// ─────────────────────────────────────────────────────────────────

TEST_CASE("RT-2 — circular arc entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("5.0,1.0,2.0,3.0,4.0,5.0,6.0;", ',', ';');
    auto r1 = parse_circular_arc_entity(tok);
    REQUIRE(r1.has_value());

    std::string s = write_circular_arc_entity(r1.value());
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_circular_arc_entity(tok2);
    REQUIRE(r2.has_value());

    CHECK_THAT(r2->zt, WithinRel(5.0));
    CHECK_THAT(r2->x1, WithinRel(1.0));
    CHECK_THAT(r2->y1, WithinRel(2.0));
    CHECK_THAT(r2->x2, WithinRel(3.0));
    CHECK_THAT(r2->y2, WithinRel(4.0));
    CHECK_THAT(r2->x3, WithinRel(5.0));
    CHECK_THAT(r2->y3, WithinRel(6.0));
}

// ─────────────────────────────────────────────────────────────────
// RT-3: Point entity round-trip
// ─────────────────────────────────────────────────────────────────

TEST_CASE("RT-3 — point entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("7.5,8.5,9.5,3;", ',', ';');
    auto r1 = parse_point_entity(tok);
    REQUIRE(r1.has_value());

    std::string s = write_point_entity(r1.value());
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_point_entity(tok2);
    REQUIRE(r2.has_value());

    CHECK_THAT(r2->coords.x, WithinRel(7.5));
    CHECK_THAT(r2->coords.y, WithinRel(8.5));
    CHECK_THAT(r2->coords.z, WithinRel(9.5));
    CHECK(r2->display_symbol.value == 3);
}

// ─────────────────────────────────────────────────────────────────
// RT-4: Composite curve entity round-trip
// ─────────────────────────────────────────────────────────────────

TEST_CASE("RT-4 — composite curve entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("3,1,3,5;", ',', ';');
    auto r1 = parse_composite_curve_entity(tok);
    REQUIRE(r1.has_value());

    std::string s = write_composite_curve_entity(r1.value());
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_composite_curve_entity(tok2);
    REQUIRE(r2.has_value());

    CHECK(r2->constituents.size() == 3);
    CHECK(r2->constituents[0].value == 1);
    CHECK(r2->constituents[1].value == 3);
    CHECK(r2->constituents[2].value == 5);
}

// ─────────────────────────────────────────────────────────────────
// RT-5: Null entity round-trip (trivial)
// ─────────────────────────────────────────────────────────────────

TEST_CASE("RT-5 -- null entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok(";", ',', ';');
    auto r1 = parse_null_entity(tok);
    REQUIRE(r1.has_value());

    std::string s = write_null_entity(r1.value());
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_null_entity(tok2);
    REQUIRE(r2.has_value());
}

// -----------------------------------------------------------------
// RT-6: Transformation matrix entity round-trip
// -----------------------------------------------------------------

TEST_CASE("RT-6 -- transformation matrix round-trip", "[writer][round-trip]") {
    // §4.21: R11,R12,R13,T1,R21,R22,R23,T2,R31,R32,R33,T3
    ParamTokenizer tok("1.0,0.0,0.0,10.0,0.0,1.0,0.0,20.0,0.0,0.0,1.0,30.0;", ',', ';');
    auto r1 = parse_transformation_matrix_entity(tok);
    REQUIRE(r1.has_value());

    std::string s = write_transformation_matrix_entity(r1.value());
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_transformation_matrix_entity(tok2);
    REQUIRE(r2.has_value());

    CHECK_THAT(r2->rotation(0, 0), WithinRel(1.0));
    CHECK_THAT(r2->translation.x, WithinRel(10.0));
    CHECK_THAT(r2->translation.y, WithinRel(20.0));
    CHECK_THAT(r2->translation.z, WithinRel(30.0));
}

// -----------------------------------------------------------------
// RT-7: Rational B-spline curve round-trip
// -----------------------------------------------------------------

TEST_CASE("RT-7 -- rational bspline curve round-trip", "[writer][round-trip]") {
    // §4.23: Degree-1 line: K=1, M=1, 4 knots, 2 weights, 2 control points
    ParamTokenizer tok(
        "1,1,0,0,1,0,"       // K,M,prop1-4
        "0.0,0.0,1.0,1.0,"   // knots (A+1 = 4)
        "1.0,1.0,"            // weights (K+1 = 2)
        "0.0,0.0,0.0,"        // control point 0
        "1.0,1.0,1.0,"        // control point 1
        "0.0,1.0,"             // v0, v1
        "0.0,0.0,0.0;",       // plane normal
        ',', ';');
    auto r1 = parse_rational_bspline_curve_entity(tok);
    REQUIRE(r1.has_value());

    std::string s = write_rational_bspline_curve_entity(r1.value());
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_rational_bspline_curve_entity(tok2);
    REQUIRE(r2.has_value());

    CHECK(r2->K == 1);
    CHECK(r2->M == 1);
    CHECK(r2->knots.size() == 4);
    CHECK(r2->control_points.size() == 2);
    CHECK_THAT(r2->control_points[1].x, WithinRel(1.0));
    CHECK_THAT(r2->v0, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r2->v1, WithinRel(1.0));
}

// -----------------------------------------------------------------
// RT-8: Trimmed surface round-trip
// -----------------------------------------------------------------

TEST_CASE("RT-8 -- trimmed surface round-trip", "[writer][round-trip]") {
    // §4.34: PTS, N1, N2, PTO, PTI1, PTI2
    ParamTokenizer tok("1,1,2,3,5,7;", ',', ';');
    auto r1 = parse_trimmed_surface_entity(tok);
    REQUIRE(r1.has_value());

    std::string s = write_trimmed_surface_entity(r1.value());
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_trimmed_surface_entity(tok2);
    REQUIRE(r2.has_value());

    CHECK(r2->pts.value == 1);
    CHECK(r2->n1 == 1);
    CHECK(r2->n2 == 2);
    CHECK(r2->pto.value == 3);
    CHECK(r2->pti.size() == 2);
    CHECK(r2->pti[0].value == 5);
    CHECK(r2->pti[1].value == 7);
}

// -----------------------------------------------------------------
// RT-9: Ruled surface round-trip
// -----------------------------------------------------------------

TEST_CASE("RT-9 -- ruled surface round-trip", "[writer][round-trip]") {
    // §4.17: DE1, DE2, DIRFLG, DEVFLG
    ParamTokenizer tok("1,3,1,1;", ',', ';');
    auto r1 = parse_ruled_surface_entity(tok);
    REQUIRE(r1.has_value());

    std::string s = write_ruled_surface_entity(r1.value());
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_ruled_surface_entity(tok2);
    REQUIRE(r2.has_value());

    CHECK(r2->de1.value == 1);
    CHECK(r2->de2.value == 3);
    CHECK(r2->dirflg == 1);
    CHECK(r2->devflg == 1);
}

// -----------------------------------------------------------------
// RT-10: Surface of revolution round-trip
// -----------------------------------------------------------------

TEST_CASE("RT-10 -- surface of revolution round-trip", "[writer][round-trip]") {
    // §4.18: L, C, SA, TA
    ParamTokenizer tok("1,3,0.0,6.283185307179586;", ',', ';');
    auto r1 = parse_surface_of_revolution_entity(tok);
    REQUIRE(r1.has_value());

    std::string s = write_surface_of_revolution_entity(r1.value());
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_surface_of_revolution_entity(tok2);
    REQUIRE(r2.has_value());

    CHECK(r2->l.value == 1);
    CHECK(r2->c.value == 3);
    CHECK_THAT(r2->sa, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r2->ta, WithinRel(6.283185307179586));
}
