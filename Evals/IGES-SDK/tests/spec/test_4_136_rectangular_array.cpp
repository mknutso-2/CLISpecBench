// Tests for §4.136 — Rectangular Array Subfigure Instance Entity (Type 412).
// Spec reference: IGES 5.3, §4.136, pages 499-500.

#include <catch2/catch_test_macros.hpp>
#include "entities/rectangular_array_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.136 PD table (page 500): DE, S, X, Y, Z, NC, NR, DX, DY,
//   AX, LC, DDF, N(1)..N(LC)
// -----------------------------------------------------------------

TEST_CASE("§4.136 — parse rectangular array 3x2", "[entity][spec-4.136]") {
    // 12 fixed fields, LC=0 so no position list
    ParamTokenizer tok("1,1.0,0.0,0.0,0.0,3,2,10.0,20.0,0.0,0,0;", ',', ';');
    auto r = parse_rectangular_array_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->de.value == 1);
    CHECK(r->s == 1.0);
    CHECK(r->position.x == 0.0);
    CHECK(r->nc == 3);
    CHECK(r->nr == 2);
    CHECK(r->dx == 10.0);
    CHECK(r->dy == 20.0);
    CHECK(r->ax == 0.0);
    CHECK(r->lc == 0);
    CHECK(r->ddf == 0);
    CHECK(r->positions.empty());
}

TEST_CASE("§4.136 — rectangular array with DO-DON'T list", "[entity][spec-4.136]") {
    // LC=2, DDF=1 (DON'T), positions 3 and 5
    ParamTokenizer tok("3,2.0,0.0,0.0,0.0,2,2,5.0,5.0,0.0,2,1,3,5;", ',', ';');
    auto r = parse_rectangular_array_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->lc == 2);
    CHECK(r->ddf == 1);
    REQUIRE(r->positions.size() == 2);
    CHECK(r->positions[0] == 3);
    CHECK(r->positions[1] == 5);
}

TEST_CASE("§4.136 — round-trip rectangular array", "[entity][spec-4.136]") {
    RectangularArrayEntity orig;
    orig.de = DEIndex{5};
    orig.s = 2.0;
    orig.position = {1.0, 2.0, 0.0};
    orig.nc = 3;
    orig.nr = 4;
    orig.dx = 10.0;
    orig.dy = 15.0;
    orig.ax = 0.5;
    orig.lc = 2;
    orig.ddf = 0;
    orig.positions = {1, 4};

    auto pd = write_rectangular_array_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_rectangular_array_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->de.value == 5);
    CHECK(r->s == 2.0);
    CHECK(r->nc == 3);
    CHECK(r->nr == 4);
    CHECK(r->dx == 10.0);
    CHECK(r->ax == 0.5);
    CHECK(r->lc == 2);
    CHECK(r->ddf == 0);
    REQUIRE(r->positions.size() == 2);
    CHECK(r->positions[0] == 1);
    CHECK(r->positions[1] == 4);
}
