// Tests for §4.137 — Circular Array Subfigure Instance Entity (Type 414).
// Spec reference: IGES 5.3, §4.137, pages 501-502.

#include <catch2/catch_test_macros.hpp>
#include "entities/circular_array_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.137 PD table (page 502): DE, NE, X, Y, Z, R, AS, AD,
//   LC, DDF, N(1)..N(LC)
// -----------------------------------------------------------------

TEST_CASE("§4.137 — parse circular array with 6 positions", "[entity][spec-4.137]") {
    // 10 fixed fields, LC=0 so display all
    ParamTokenizer tok("3,6,0.0,0.0,0.0,10.0,0.0,1.0472,0,0;", ',', ';');
    auto r = parse_circular_array_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->de.value == 3);
    CHECK(r->ne == 6);
    CHECK(r->center.x == 0.0);
    CHECK(r->r == 10.0);
    CHECK(r->as == 0.0);
    CHECK(r->ad == 1.0472);
    CHECK(r->lc == 0);
    CHECK(r->ddf == 0);
    CHECK(r->positions.empty());
}

TEST_CASE("§4.137 — circular array with DO-DON'T list", "[entity][spec-4.137]") {
    // LC=2, DDF=1 (DON'T), positions 2 and 4
    ParamTokenizer tok("5,4,0.0,0.0,0.0,5.0,0.0,1.5708,2,1,2,4;", ',', ';');
    auto r = parse_circular_array_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ne == 4);
    CHECK(r->lc == 2);
    CHECK(r->ddf == 1);
    REQUIRE(r->positions.size() == 2);
    CHECK(r->positions[0] == 2);
    CHECK(r->positions[1] == 4);
}

TEST_CASE("§4.137 — round-trip circular array", "[entity][spec-4.137]") {
    CircularArrayEntity orig;
    orig.de = DEIndex{7};
    orig.ne = 8;
    orig.center = {1.0, 2.0, 0.0};
    orig.r = 15.0;
    orig.as = 0.5;
    orig.ad = 0.7854;
    orig.lc = 1;
    orig.ddf = 0;
    orig.positions = {3};

    auto pd = write_circular_array_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_circular_array_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->de.value == 7);
    CHECK(r->ne == 8);
    CHECK(r->r == 15.0);
    CHECK(r->as == 0.5);
    CHECK(r->ad == 0.7854);
    CHECK(r->lc == 1);
    CHECK(r->ddf == 0);
    REQUIRE(r->positions.size() == 1);
    CHECK(r->positions[0] == 3);
}
