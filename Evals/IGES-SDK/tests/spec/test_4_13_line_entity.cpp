// Tests for §4.13 — Line Entity (Type 110).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/line_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// ─────────────────────────────────────────────────────────────────
// §4.13: "A line is a bounded, connected portion of a parent
//   straight line ... defined by its end points"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.13 — parse line entity from PD", "[entity][spec-4.13]") {
    // §4.13: "Parameters: X1,Y1,Z1 (start point), X2,Y2,Z2 (terminate point)"
    ParamTokenizer tok("1.0,2.0,3.0,4.0,5.0,6.0;", ',', ';');
    auto r = parse_line_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r.value().start.x, WithinRel(1.0));
    CHECK_THAT(r.value().start.y, WithinRel(2.0));
    CHECK_THAT(r.value().start.z, WithinRel(3.0));
    CHECK_THAT(r.value().terminate.x, WithinRel(4.0));
    CHECK_THAT(r.value().terminate.y, WithinRel(5.0));
    CHECK_THAT(r.value().terminate.z, WithinRel(6.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.13: "Each end point is specified relative to the definition
//   space by triple coordinates"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.13 — line at origin", "[entity][spec-4.13]") {
    // §4.13: "Each end point is specified ... by triple coordinates"
    ParamTokenizer tok("0.,0.,0.,0.,0.,0.;", ',', ';');
    auto r = parse_line_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r.value().start.x, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r.value().terminate.x, WithinAbs(0.0, 1e-15));
}

TEST_CASE("§4.13 — line with negative coordinates", "[entity][spec-4.13]") {
    // §4.13: "Each end point is specified ... by triple coordinates"
    ParamTokenizer tok("-1.5,2.5,-3.5,4.5,-5.5,6.5;", ',', ';');
    auto r = parse_line_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r.value().start.x, WithinRel(-1.5));
    CHECK_THAT(r.value().start.y, WithinRel(2.5));
    CHECK_THAT(r.value().start.z, WithinRel(-3.5));
}

// ─────────────────────────────────────────────────────────────────
// §4.13: "For the line entity, the parametrization is
//   C(t) = P1 + t*(P2 - P1) for 0 <= t <= 1"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.13 — parameterization at t=0 gives start point", "[entity][spec-4.13]") {
    // §4.13: "C(t) = P1 + t*(P2 - P1) ... C(0) = P1"
    LineEntity line{{1,2,3}, {4,5,6}};
    auto p = line.evaluate(0.0);
    CHECK_THAT(p.x, WithinRel(1.0));
    CHECK_THAT(p.y, WithinRel(2.0));
    CHECK_THAT(p.z, WithinRel(3.0));
}

TEST_CASE("§4.13 — parameterization at t=1 gives terminate point", "[entity][spec-4.13]") {
    // §4.13: "C(t) = P1 + t*(P2 - P1) ... C(1) = P2"
    LineEntity line{{1,2,3}, {4,5,6}};
    auto p = line.evaluate(1.0);
    CHECK_THAT(p.x, WithinRel(4.0));
    CHECK_THAT(p.y, WithinRel(5.0));
    CHECK_THAT(p.z, WithinRel(6.0));
}

TEST_CASE("§4.13 — parameterization at t=0.5 gives midpoint", "[entity][spec-4.13]") {
    // §4.13: "C(t) = P1 + t*(P2 - P1) ... C(0.5) = midpoint"
    LineEntity line{{0,0,0}, {10,0,0}};
    auto p = line.evaluate(0.5);
    CHECK_THAT(p.x, WithinRel(5.0));
    CHECK_THAT(p.y, WithinAbs(0.0, 1e-15));
    CHECK_THAT(p.z, WithinAbs(0.0, 1e-15));
}

// ─────────────────────────────────────────────────────────────────
// §3.2.5: "All curves shall have non-zero arc length"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§3.2.5 — line arc length is non-zero for distinct points", "[entity][spec-3.2.5]") {
    // §3.2.5: "All curves shall have non-zero arc length"
    LineEntity line{{0,0,0}, {3,4,0}};
    Real len = (line.terminate - line.start).length();
    CHECK_THAT(len, WithinRel(5.0));
}
