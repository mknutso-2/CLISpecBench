// Tests for §4.78 — Network Subfigure Definition Entity (Type 320).
// Spec reference: IGES 5.3, §4.78, page 334.

#include <catch2/catch_test_macros.hpp>
#include "entities/network_subfigure_definition_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.78: "Parameters: DEPTH, NAME, NA, APTR(1..NA), TF, PRD,
//   DPTR, NC, CPTR(1..NC)"
// -----------------------------------------------------------------

TEST_CASE("§4.78 — parse network subfigure definition", "[entity][spec-4.78]") {
    // §4.78 PD: "Index 1: DEPTH, 2: NAME, 3: NA, 4..3+NA: APTR(i),
    //   4+NA: TF, 5+NA: PRD, 6+NA: DPTR, 7+NA: NC, 8+NA..7+NA+NC: CPTR(i)"
    ParamTokenizer tok("2,4HCOMP,1,5,1,3HPRD,7,2,9,11;", ',', ';');
    auto r = parse_network_subfigure_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->depth == 2);
    CHECK(r->name == "COMP");
    CHECK(r->na == 1);
    CHECK(r->associated.size() == 1);
    CHECK(r->associated[0].value == 5);
    CHECK(r->tf == 1);
    CHECK(r->prd == "PRD");
    CHECK(r->dptr.value == 7);
    CHECK(r->nc == 2);
    CHECK(r->connects.size() == 2);
    CHECK(r->connects[0].value == 9);
    CHECK(r->connects[1].value == 11);
}

// -----------------------------------------------------------------
// §4.78: Network subfigure with zero associated entities
// -----------------------------------------------------------------

TEST_CASE("§4.78 — zero associated entities", "[entity][spec-4.78]") {
    // §4.78: NA can be zero
    ParamTokenizer tok("1,3HFOO,0,0,2HXY,3,0;", ',', ';');
    auto r = parse_network_subfigure_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->na == 0);
    CHECK(r->associated.empty());
    CHECK(r->nc == 0);
    CHECK(r->connects.empty());
}

// -----------------------------------------------------------------
// §4.78: "TF: Type flag" (0=not specified, 1=logical, 2=physical)
// -----------------------------------------------------------------

TEST_CASE("§4.78 — type flag values", "[entity][spec-4.78]") {
    // §4.78: "TF: 0=Not specified, 1=Logical design, 2=Physical design"
    NetworkSubfigureDefinitionEntity e;
    e.depth = 1; e.name = "N";
    e.tf = 2;
    e.prd = "U1"; e.dptr = DEIndex{1};

    auto pd = write_network_subfigure_definition_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_network_subfigure_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->tf == 2);
}

// -----------------------------------------------------------------
// §4.78: Multiple associated entities and connect points
// -----------------------------------------------------------------

TEST_CASE("§4.78 — multiple associated entities and connects", "[entity][spec-4.78]") {
    NetworkSubfigureDefinitionEntity e;
    e.depth = 3; e.name = "CHIP";
    e.na = 2; e.associated = {DEIndex{10}, DEIndex{12}};
    e.tf = 1; e.prd = "IC1"; e.dptr = DEIndex{20};
    e.nc = 3; e.connects = {DEIndex{30}, DEIndex{32}, DEIndex{34}};

    auto pd = write_network_subfigure_definition_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_network_subfigure_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->na == 2);
    CHECK(r->associated.size() == 2);
    CHECK(r->associated[0].value == 10);
    CHECK(r->associated[1].value == 12);
    CHECK(r->nc == 3);
    CHECK(r->connects.size() == 3);
    CHECK(r->connects[0].value == 30);
    CHECK(r->connects[1].value == 32);
    CHECK(r->connects[2].value == 34);
}

// -----------------------------------------------------------------
// Round-trip: write then parse
// -----------------------------------------------------------------

TEST_CASE("§4.78 — round-trip network subfigure definition", "[entity][spec-4.78]") {
    NetworkSubfigureDefinitionEntity orig;
    orig.depth = 1; orig.name = "RESISTOR";
    orig.na = 1; orig.associated = {DEIndex{5}};
    orig.tf = 0; orig.prd = "R1"; orig.dptr = DEIndex{7};
    orig.nc = 2; orig.connects = {DEIndex{9}, DEIndex{11}};

    auto pd = write_network_subfigure_definition_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_network_subfigure_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->depth == orig.depth);
    CHECK(r->name == orig.name);
    CHECK(r->na == orig.na);
    CHECK(r->associated[0].value == 5);
    CHECK(r->tf == orig.tf);
    CHECK(r->prd == orig.prd);
    CHECK(r->dptr.value == orig.dptr.value);
    CHECK(r->nc == orig.nc);
    CHECK(r->connects[0].value == 9);
    CHECK(r->connects[1].value == 11);
}
