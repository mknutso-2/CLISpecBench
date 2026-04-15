// Tests for §4.20 — Direction Entity (Type 123).
// Spec reference: IGES 5.3, §4.20, page 112.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/direction_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"
#include <cmath>

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// ─────────────────────────────────────────────────────────────────
// §4.20: "Parameters: X, Y, Z — direction ratios"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.20 — parse direction entity (3 parameters)", "[entity][spec-4.20]") {
    // §4.20: "Index 1: X, Index 2: Y, Index 3: Z — Direction ratio
    //   with respect to X/Y/Z axis"
    ParamTokenizer tok("1.0,0.0,0.0;", ',', ';');
    auto r = parse_direction_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->x, WithinRel(1.0));
    CHECK_THAT(r->y, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r->z, WithinAbs(0.0, 1e-15));
}

// ─────────────────────────────────────────────────────────────────
// §4.20: "x^2 + y^2 + z^2 > 0" (non-zero vector)
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.20 — non-axis-aligned direction", "[entity][spec-4.20]") {
    // §4.20: Direction ratios need not be unit length per spec
    ParamTokenizer tok("1.0,2.0,3.0;", ',', ';');
    auto r = parse_direction_entity(tok);
    REQUIRE(r.has_value());
    Real len_sq = r->x * r->x + r->y * r->y + r->z * r->z;
    CHECK(len_sq > 0.0);  // §4.20: "x^2 + y^2 + z^2 > 0"
    CHECK_THAT(r->x, WithinRel(1.0));
    CHECK_THAT(r->y, WithinRel(2.0));
    CHECK_THAT(r->z, WithinRel(3.0));
}

TEST_CASE("§4.20 — unit Z direction", "[entity][spec-4.20]") {
    // §4.20: Direction along Z axis
    ParamTokenizer tok("0.0,0.0,1.0;", ',', ';');
    auto r = parse_direction_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->z, WithinRel(1.0));
}

// ─────────────────────────────────────────────────────────────────
// Round-trip: write then parse
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.20 — round-trip direction entity", "[entity][spec-4.20]") {
    DirectionEntity orig;
    orig.x = 0.5773502691896258;
    orig.y = 0.5773502691896258;
    orig.z = 0.5773502691896258;

    auto pd = write_direction_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_direction_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->x, WithinRel(orig.x));
    CHECK_THAT(r->y, WithinRel(orig.y));
    CHECK_THAT(r->z, WithinRel(orig.z));
}
