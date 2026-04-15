// Tests for §4.12 — Plane Entity (Type 108).
// Spec reference: IGES 5.3, §4.12, pages 87-89.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/plane_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// ─────────────────────────────────────────────────────────────────
// §4.12: "A*Xt + B*Yt + C*Zt = D, where at least one of A,B,C
//   is nonzero"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.12 — parse unbounded plane (Form 0)", "[entity][spec-4.12]") {
    // §4.12: "Unbounded Plane Entity (Type 108, Form 0)"
    // PD: A, B, C, D, PTR(=0), X, Y, Z, SIZE
    ParamTokenizer tok("0.0,0.0,1.0,5.0,0,0.0,0.0,5.0,1.0;", ',', ';');
    auto r = parse_plane_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->A, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r->B, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r->C, WithinRel(1.0));
    CHECK_THAT(r->D, WithinRel(5.0));
    CHECK(r->ptr.value == 0);  // unbounded => PTR = 0
    CHECK_THAT(r->z, WithinRel(5.0));
    CHECK_THAT(r->size, WithinRel(1.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.12: "Form 0: Plane is unbounded. PTR shall be zero."
// §4.12: "Form 1: Bounded planar portion. PTR shall not be zero."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.12 — bounded plane has nonzero PTR", "[entity][spec-4.12]") {
    // §4.12: "Forms 1 and -1: Bounded. PTR ... pointer to the DE
    //   of the closed curve entity"
    ParamTokenizer tok("1.0,0.0,0.0,0.0,5,0.0,0.0,0.0,0.0;", ',', ';');
    auto r = parse_plane_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ptr.value == 5);
}

// ─────────────────────────────────────────────────────────────────
// §4.12: Plane coefficients define A*X+B*Y+C*Z=D
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.12 — XY plane through origin", "[entity][spec-4.12]") {
    // §4.12: Z=0 plane => A=0,B=0,C=1,D=0
    PlaneEntity p;
    p.A = 0.0; p.B = 0.0; p.C = 1.0; p.D = 0.0;
    // Point (x,y,0) satisfies: 0*x + 0*y + 1*0 = 0
    CHECK_THAT(p.A * 3.0 + p.B * 4.0 + p.C * 0.0, WithinAbs(p.D, 1e-15));
}

TEST_CASE("§4.12 — tilted plane", "[entity][spec-4.12]") {
    // §4.12: X + Y + Z = 1 => A=1,B=1,C=1,D=1
    PlaneEntity p;
    p.A = 1.0; p.B = 1.0; p.C = 1.0; p.D = 1.0;
    // Point (1/3, 1/3, 1/3) satisfies: 1/3 + 1/3 + 1/3 = 1
    Real val = p.A * (1.0/3.0) + p.B * (1.0/3.0) + p.C * (1.0/3.0);
    CHECK_THAT(val, WithinRel(p.D));
}

// ─────────────────────────────────────────────────────────────────
// Round-trip: write then parse
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.12 — round-trip plane entity", "[entity][spec-4.12]") {
    PlaneEntity orig;
    orig.A = 0.0; orig.B = 0.0; orig.C = 1.0; orig.D = 10.0;
    orig.ptr = DEIndex{0};
    orig.x = 5.0; orig.y = 5.0; orig.z = 10.0; orig.size = 2.0;

    auto pd = write_plane_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_plane_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->A, WithinAbs(orig.A, 1e-15));
    CHECK_THAT(r->C, WithinRel(orig.C));
    CHECK_THAT(r->D, WithinRel(orig.D));
    CHECK(r->ptr.value == orig.ptr.value);
    CHECK_THAT(r->x, WithinRel(orig.x));
    CHECK_THAT(r->size, WithinRel(orig.size));
}
