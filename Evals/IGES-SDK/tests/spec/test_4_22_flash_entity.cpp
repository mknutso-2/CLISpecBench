// Tests for §4.22 — Flash Entity (Type 125).
// Spec reference: IGES 5.3, §4.22, pages 120-122.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/flash_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// ─────────────────────────────────────────────────────────────────
// §4.22: "Parameters: X, Y, DIM1, DIM2, ROT, DE"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.22 — parse flash entity (6 parameters)", "[entity][spec-4.22]") {
    // §4.22 PD: "Index 1: X, 2: Y, 3: DIM1, 4: DIM2, 5: ROT, 6: DE"
    ParamTokenizer tok("10.0,20.0,5.0,3.0,0.785,0;", ',', ';');
    auto r = parse_flash_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->x, WithinRel(10.0));
    CHECK_THAT(r->y, WithinRel(20.0));
    CHECK_THAT(r->dim1, WithinRel(5.0));
    CHECK_THAT(r->dim2, WithinRel(3.0));
    CHECK_THAT(r->rot, WithinRel(0.785));
    CHECK(r->de.value == 0);
}

// ─────────────────────────────────────────────────────────────────
// §4.22: "Form 1: Circular. DIMENSION 1 = DIAMETER OF CIRCLE"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.22 — circular flash has diameter in DIM1", "[entity][spec-4.22]") {
    // §4.22: Form 1 — DIM1 = diameter, DIM2 = null or zero
    FlashEntity e;
    e.x = 0.0; e.y = 0.0;
    e.dim1 = 2.5;  // diameter
    e.dim2 = 0.0;
    e.rot = 0.0;
    auto pd = write_flash_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_flash_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->dim1, WithinRel(2.5));
    CHECK_THAT(r->dim2, WithinAbs(0.0, 1e-15));
}

// ─────────────────────────────────────────────────────────────────
// §4.22: "Form 2: Rectangle. DIMENSION 1 = X AXIS LENGTH,
//   DIMENSION 2 = Y AXIS LENGTH"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.22 — rectangular flash has X and Y lengths", "[entity][spec-4.22]") {
    // §4.22: Form 2 — DIM1 = X axis length, DIM2 = Y axis length
    FlashEntity e;
    e.x = 5.0; e.y = 5.0;
    e.dim1 = 10.0;  // X length
    e.dim2 = 6.0;   // Y length
    e.rot = 0.0;
    auto pd = write_flash_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_flash_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->dim1, WithinRel(10.0));
    CHECK_THAT(r->dim2, WithinRel(6.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.22: "Form 0: Defined by referenced entity. DE ... pointer to
//   the DE of the referenced entity"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.22 — form 0 flash references external entity", "[entity][spec-4.22]") {
    // §4.22: Form 0 — closed area defined by referenced entity
    ParamTokenizer tok("1.0,2.0,0.0,0.0,0.0,7;", ',', ';');
    auto r = parse_flash_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->de.value == 7);
}

// ─────────────────────────────────────────────────────────────────
// §4.22: ROT is rotation about reference point in radians
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.22 — rotation parameter in radians", "[entity][spec-4.22]") {
    // §4.22: "ROT: Rotation of flash about reference point in radians"
    FlashEntity e;
    e.x = 0.0; e.y = 0.0;
    e.dim1 = 4.0; e.dim2 = 2.0;
    e.rot = 1.5707963267948966;  // pi/2
    auto pd = write_flash_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_flash_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->rot, WithinRel(1.5707963267948966));
}

// ─────────────────────────────────────────────────────────────────
// Round-trip: write then parse
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.22 — round-trip flash entity", "[entity][spec-4.22]") {
    FlashEntity orig;
    orig.x = 15.5; orig.y = 25.3;
    orig.dim1 = 8.0; orig.dim2 = 4.0;
    orig.rot = 0.5; orig.de = DEIndex{11};

    auto pd = write_flash_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_flash_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->x, WithinRel(orig.x));
    CHECK_THAT(r->y, WithinRel(orig.y));
    CHECK_THAT(r->dim1, WithinRel(orig.dim1));
    CHECK_THAT(r->dim2, WithinRel(orig.dim2));
    CHECK_THAT(r->rot, WithinRel(orig.rot));
    CHECK(r->de.value == orig.de.value);
}
