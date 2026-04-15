// Tests for §4.74 — Text Font Definition Entity (Type 310).
// Spec reference: IGES 5.3, §4.74, pages 323-326.

#include <catch2/catch_test_macros.hpp>
#include "entities/text_font_definition_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.74: "Parameters: FC, FNAME, SF, SCALE, N,
//   {AC, NX, NY, NM, {PF, X, Y} x NM} x N"
// -----------------------------------------------------------------

TEST_CASE("§4.74 — parse single character font definition", "[entity][spec-4.74]") {
    // §4.74 PD: FC=1, FNAME="STAND", SF=0 (no supersede), SCALE=8, N=1,
    //   AC=65 ('A'), NX=8, NY=0, NM=2, {PF=0,X=0,Y=0}, {PF=0,X=4,Y=8}
    ParamTokenizer tok("1,5HSTAND,0,8,1,"
                       "65,8,0,2,0,0,0,0,4,8;", ',', ';');
    auto r = parse_text_font_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->fc == 1);
    CHECK(r->fname == "STAND");
    CHECK(r->sf == 0);
    CHECK(r->scale == 8);
    CHECK(r->n == 1);

    REQUIRE(r->characters.size() == 1);
    auto const& ch = r->characters[0];
    CHECK(ch.ac == 65);
    CHECK(ch.nx == 8);
    CHECK(ch.ny == 0);
    CHECK(ch.nm == 2);
    REQUIRE(ch.motions.size() == 2);
    CHECK(ch.motions[0].pf == 0);
    CHECK(ch.motions[0].x == 0);
    CHECK(ch.motions[0].y == 0);
    CHECK(ch.motions[1].pf == 0);
    CHECK(ch.motions[1].x == 4);
    CHECK(ch.motions[1].y == 8);
}

// -----------------------------------------------------------------
// §4.74: pen up flag (PF=1) means "lift pen"
// -----------------------------------------------------------------

TEST_CASE("§4.74 — pen up/down flag", "[entity][spec-4.74]") {
    // FC=2, FNAME="TEST", SF=0, SCALE=10, N=1,
    //   AC=66 ('B'), NX=10, NY=0, NM=3,
    //   {PF=0,X=0,Y=0}, {PF=1,X=5,Y=5}, {PF=0,X=10,Y=0}
    ParamTokenizer tok("2,4HTEST,0,10,1,"
                       "66,10,0,3,0,0,0,1,5,5,0,10,0;", ',', ';');
    auto r = parse_text_font_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->characters[0].motions[0].pf == 0);
    CHECK(r->characters[0].motions[1].pf == 1);
    CHECK(r->characters[0].motions[2].pf == 0);
}

// -----------------------------------------------------------------
// §4.74: multiple characters in one definition
// -----------------------------------------------------------------

TEST_CASE("§4.74 — multiple characters", "[entity][spec-4.74]") {
    // FC=1, FNAME="MY", SF=0, SCALE=8, N=2,
    //   char1: AC=65, NX=8, NY=0, NM=1, {0,4,8}
    //   char2: AC=66, NX=9, NY=0, NM=1, {0,2,4}
    ParamTokenizer tok("1,2HMY,0,8,2,"
                       "65,8,0,1,0,4,8,"
                       "66,9,0,1,0,2,4;", ',', ';');
    auto r = parse_text_font_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->n == 2);
    REQUIRE(r->characters.size() == 2);
    CHECK(r->characters[0].ac == 65);
    CHECK(r->characters[1].ac == 66);
    CHECK(r->characters[1].nx == 9);
}

// -----------------------------------------------------------------
// Round-trip: write then parse
// -----------------------------------------------------------------

TEST_CASE("§4.74 — round-trip text font definition", "[entity][spec-4.74]") {
    TextFontDefinitionEntity orig;
    orig.fc = 3;
    orig.fname = "MYFONT";
    orig.sf = 0;
    orig.scale = 12;
    orig.n = 1;

    CharacterDefinition ch;
    ch.ac = 67;
    ch.nx = 11;
    ch.ny = 0;
    ch.nm = 3;
    ch.motions = {{0, 0, 0}, {0, 5, 10}, {1, 10, 0}};
    orig.characters.push_back(ch);

    auto pd = write_text_font_definition_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_text_font_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->fc == 3);
    CHECK(r->fname == "MYFONT");
    CHECK(r->sf == 0);
    CHECK(r->scale == 12);
    CHECK(r->n == 1);

    REQUIRE(r->characters.size() == 1);
    auto const& rc = r->characters[0];
    CHECK(rc.ac == 67);
    CHECK(rc.nx == 11);
    CHECK(rc.nm == 3);
    CHECK(rc.motions[0].x == 0);
    CHECK(rc.motions[1].x == 5);
    CHECK(rc.motions[2].pf == 1);
    CHECK(rc.motions[2].x == 10);
}
