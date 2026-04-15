// Tests for §4.3 — Circular Arc Entity (Type 100).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/circular_arc_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include <cmath>
#include <numbers>

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// ─────────────────────────────────────────────────────────────────
// §4.3: "Parameters: ZT, X1, Y1, X2, Y2, X3, Y3"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.3 — parse circular arc entity", "[entity][spec-4.3]") {
    // §4.3: "Parameters: ZT (Z displacement), X1,Y1 (center),
    //   X2,Y2 (start), X3,Y3 (terminate)"
    ParamTokenizer tok("0.0,0.0,0.0,1.0,0.0,0.0,1.0;", ',', ';');
    auto r = parse_circular_arc_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r.value().zt, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r.value().x1, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r.value().y1, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r.value().x2, WithinRel(1.0));
    CHECK_THAT(r.value().y2, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r.value().x3, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r.value().y3, WithinRel(1.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.3: "A circular arc ... lies in a plane either coincident
//   with, or parallel to, the XT,YT plane"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.3 — ZT displacement places arc in parallel plane", "[entity][spec-4.3]") {
    // §4.3: "A circular arc ... lies in a plane ... parallel to, the
    //   XT,YT plane ... ZT is the Z coordinate of the plane"
    ParamTokenizer tok("5.0,0.0,0.0,1.0,0.0,0.0,1.0;", ',', ';');
    auto r = parse_circular_arc_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r.value().zt, WithinRel(5.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.3: "the radius of the arc is the Euclidean distance from
//   the center to the start point"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.3 — radius computed from center and start point", "[entity][spec-4.3]") {
    // §4.3: "the radius of the arc is the Euclidean distance from
    //   the center to the start point"
    CircularArcEntity arc;
    arc.x1 = 0.0; arc.y1 = 0.0;
    arc.x2 = 3.0; arc.y2 = 4.0;
    arc.x3 = -3.0; arc.y3 = -4.0;
    CHECK_THAT(arc.radius(), WithinRel(5.0));
}

TEST_CASE("§4.3 — unit circle radius", "[entity][spec-4.3]") {
    // §4.3: "the radius of the arc is the Euclidean distance from
    //   the center to the start point"
    CircularArcEntity arc;
    arc.x1 = 0.0; arc.y1 = 0.0;
    arc.x2 = 1.0; arc.y2 = 0.0;
    arc.x3 = 0.0; arc.y3 = 1.0;
    CHECK_THAT(arc.radius(), WithinRel(1.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.3: "The arc is defined by listing the center point, the
//   start point first, followed by the terminate point in the
//   counterclockwise direction"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.3 — start and terminate angles for quarter arc", "[entity][spec-4.3]") {
    // §4.3: "start point first, followed by the terminate point in
    //   the counterclockwise direction"
    CircularArcEntity arc;
    arc.x1 = 0.0; arc.y1 = 0.0;
    arc.x2 = 1.0; arc.y2 = 0.0;
    arc.x3 = 0.0; arc.y3 = 1.0;
    CHECK_THAT(arc.start_angle(), WithinAbs(0.0, 1e-12));
    CHECK_THAT(arc.terminate_angle(), WithinAbs(std::numbers::pi / 2.0, 1e-12));
}

// ─────────────────────────────────────────────────────────────────
// §4.3: "A full circle is defined by making the start and
//   terminate points identical"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.3 — full circle when start equals terminate", "[entity][spec-4.3]") {
    // §4.3: "A full circle is defined by making the start and
    //   terminate points identical"
    CircularArcEntity arc;
    arc.x1 = 0.0; arc.y1 = 0.0;
    arc.x2 = 1.0; arc.y2 = 0.0;
    arc.x3 = 1.0; arc.y3 = 0.0;
    CHECK(arc.is_full_circle());
}

TEST_CASE("§4.3 — not full circle when start differs from terminate", "[entity][spec-4.3]") {
    // §4.3: When start and terminate differ, it is a partial arc
    CircularArcEntity arc;
    arc.x1 = 0.0; arc.y1 = 0.0;
    arc.x2 = 1.0; arc.y2 = 0.0;
    arc.x3 = 0.0; arc.y3 = 1.0;
    CHECK(!arc.is_full_circle());
}

// ─────────────────────────────────────────────────────────────────
// §4.3: "The parameterization for the circular arc entity is:
//   C(t) = (X1 + R*cos(t), Y1 + R*sin(t), ZT)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.3 — evaluate at start angle returns start point", "[entity][spec-4.3]") {
    // §4.3: "C(t) = (X1 + R*cos(t), Y1 + R*sin(t), ZT)"
    CircularArcEntity arc;
    arc.zt = 0.0;
    arc.x1 = 0.0; arc.y1 = 0.0;
    arc.x2 = 1.0; arc.y2 = 0.0;
    arc.x3 = 0.0; arc.y3 = 1.0;
    auto p = arc.evaluate(arc.start_angle());
    CHECK_THAT(p.x, WithinAbs(1.0, 1e-12));
    CHECK_THAT(p.y, WithinAbs(0.0, 1e-12));
    CHECK_THAT(p.z, WithinAbs(0.0, 1e-12));
}

TEST_CASE("§4.3 — evaluate at terminate angle returns terminate point", "[entity][spec-4.3]") {
    // §4.3: "C(t) = (X1 + R*cos(t), Y1 + R*sin(t), ZT)"
    CircularArcEntity arc;
    arc.zt = 0.0;
    arc.x1 = 0.0; arc.y1 = 0.0;
    arc.x2 = 1.0; arc.y2 = 0.0;
    arc.x3 = 0.0; arc.y3 = 1.0;
    auto p = arc.evaluate(arc.terminate_angle());
    CHECK_THAT(p.x, WithinAbs(0.0, 1e-12));
    CHECK_THAT(p.y, WithinAbs(1.0, 1e-12));
}

// ─────────────────────────────────────────────────────────────────
// §4.3: ZT is included as the Z coordinate in evaluation
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.3 — evaluate includes ZT in Z coordinate", "[entity][spec-4.3]") {
    // §4.3: "C(t) = (X1 + R*cos(t), Y1 + R*sin(t), ZT)"
    CircularArcEntity arc;
    arc.zt = 7.5;
    arc.x1 = 0.0; arc.y1 = 0.0;
    arc.x2 = 1.0; arc.y2 = 0.0;
    arc.x3 = 0.0; arc.y3 = 1.0;
    auto p = arc.evaluate(arc.start_angle());
    CHECK_THAT(p.z, WithinRel(7.5));
}
