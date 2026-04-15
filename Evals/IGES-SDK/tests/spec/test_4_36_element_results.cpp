// Tests for §4.36 — Element Results Entity (Type 148).
// Spec reference: IGES 5.3, §4.36, pages 171-173.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/element_results_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;

// -----------------------------------------------------------------
// §4.36: "Parameters: GNOTE, SCN, TIME, NV, RRF, NE,
//   {EN, EP, ITOP, NL, DLF, NRL, RDRL(1..NRL), NUMV, V(1..NUMV)} x NE"
// -----------------------------------------------------------------

TEST_CASE("§4.36 — parse centroidal results (RRF=1)", "[entity][spec-4.36]") {
    // §4.36 PD: GNOTE=1, SCN=0, TIME=0.0, NV=3, RRF=1, NE=1,
    //   EN=101, EP=3, ITOP=2, NL=1, DLF=0, NRL=1, RDRL(1)=0,
    //   NUMV=3, V(1..3)=1.5,2.5,3.5
    ParamTokenizer tok("1,0,0.0,3,1,1,"
                       "101,3,2,1,0,1,0,"
                       "3,1.5,2.5,3.5;", ',', ';');
    auto r = parse_element_results_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->gnote.value == 1);
    CHECK(r->scn == 0);
    CHECK_THAT(r->time, WithinRel(0.0, 1e-10));
    CHECK(r->nv == 3);
    CHECK(r->rrf == 1);
    CHECK(r->ne == 1);

    REQUIRE(r->elements.size() == 1);
    auto const& e = r->elements[0];
    CHECK(e.en == 101);
    CHECK(e.ep.value == 3);
    CHECK(e.itop == 2);
    CHECK(e.nl == 1);
    CHECK(e.dlf == 0);
    CHECK(e.nrl == 1);
    REQUIRE(e.rdrl.size() == 1);
    CHECK(e.rdrl[0] == 0);
    CHECK(e.numv == 3);
    REQUIRE(e.values.size() == 3);
    CHECK_THAT(e.values[0], WithinRel(1.5));
    CHECK_THAT(e.values[1], WithinRel(2.5));
    CHECK_THAT(e.values[2], WithinRel(3.5));
}

// -----------------------------------------------------------------
// §4.36: "RRF=0 ... These are the node numbers for this FEM element
//   at which results values are reported. There are NRL of them."
// -----------------------------------------------------------------

TEST_CASE("§4.36 — node-based results (RRF=0) with multiple report locations", "[entity][spec-4.36]") {
    // §4.36 PD: GNOTE=5, SCN=1, TIME=10.0, NV=2, RRF=0, NE=1,
    //   EN=200, EP=7, ITOP=3, NL=1, DLF=0, NRL=2, RDRL(1..2)=1,2,
    //   NUMV=4, V(1..4)=10.0,20.0,30.0,40.0
    //   (NV=2, NL=1, NRL=2 -> NUMV = 2*1*2 = 4)
    ParamTokenizer tok("5,1,10.0,2,0,1,"
                       "200,7,3,1,0,2,1,2,"
                       "4,10.0,20.0,30.0,40.0;", ',', ';');
    auto r = parse_element_results_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->gnote.value == 5);
    CHECK(r->scn == 1);
    CHECK_THAT(r->time, WithinRel(10.0));
    CHECK(r->nv == 2);
    CHECK(r->rrf == 0);
    CHECK(r->ne == 1);

    REQUIRE(r->elements.size() == 1);
    auto const& e = r->elements[0];
    CHECK(e.en == 200);
    CHECK(e.nrl == 2);
    CHECK(e.rdrl[0] == 1);
    CHECK(e.rdrl[1] == 2);
    CHECK(e.numv == 4);
    REQUIRE(e.values.size() == 4);
    CHECK_THAT(e.values[0], WithinRel(10.0));
    CHECK_THAT(e.values[1], WithinRel(20.0));
    CHECK_THAT(e.values[2], WithinRel(30.0));
    CHECK_THAT(e.values[3], WithinRel(40.0));
}

// -----------------------------------------------------------------
// §4.36: multiple elements in one entity
// -----------------------------------------------------------------

TEST_CASE("§4.36 — multiple FEM elements", "[entity][spec-4.36]") {
    // Two elements, each with NV=1, NL=1, NRL=1 (centroidal), NUMV=1
    ParamTokenizer tok("1,0,0.0,1,1,2,"
                       "10,3,1,1,0,1,0,1,100.0,"
                       "20,5,1,1,0,1,0,1,200.0;", ',', ';');
    auto r = parse_element_results_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ne == 2);
    REQUIRE(r->elements.size() == 2);
    CHECK(r->elements[0].en == 10);
    CHECK_THAT(r->elements[0].values[0], WithinRel(100.0));
    CHECK(r->elements[1].en == 20);
    CHECK_THAT(r->elements[1].values[0], WithinRel(200.0));
}

// -----------------------------------------------------------------
// §4.36: "NUMV = NV*NL*NRL" — multi-layer results
// -----------------------------------------------------------------

TEST_CASE("§4.36 — multi-layer results (NL > 1)", "[entity][spec-4.36]") {
    // NV=2, NL=2, NRL=1 -> NUMV = 2*2*1 = 4
    // Column-major: V(J=1,K=1,L=1), V(J=2,K=1,L=1), V(J=1,K=2,L=1), V(J=2,K=2,L=1)
    ParamTokenizer tok("1,0,5.0,2,1,1,"
                       "50,3,4,2,4,1,0,"
                       "4,1.0,2.0,3.0,4.0;", ',', ';');
    auto r = parse_element_results_entity(tok);
    REQUIRE(r.has_value());

    auto const& e = r->elements[0];
    CHECK(e.nl == 2);
    CHECK(e.dlf == 4);
    CHECK(e.numv == 4);
    REQUIRE(e.values.size() == 4);
    CHECK_THAT(e.values[0], WithinRel(1.0));
    CHECK_THAT(e.values[1], WithinRel(2.0));
    CHECK_THAT(e.values[2], WithinRel(3.0));
    CHECK_THAT(e.values[3], WithinRel(4.0));
}

// -----------------------------------------------------------------
// Round-trip: write then parse
// -----------------------------------------------------------------

TEST_CASE("§4.36 — round-trip element results", "[entity][spec-4.36]") {
    ElementResultsEntity orig;
    orig.gnote = DEIndex{9};
    orig.scn = 2;
    orig.time = 25.5;
    orig.nv = 3;
    orig.rrf = 0;
    orig.ne = 1;

    ElementResultsElement elem;
    elem.en = 42;
    elem.ep = DEIndex{11};
    elem.itop = 5;
    elem.nl = 1;
    elem.dlf = 0;
    elem.nrl = 2;
    elem.rdrl = {3, 7};
    elem.numv = 6;  // NV(3) * NL(1) * NRL(2) = 6
    elem.values = {1.1, 2.2, 3.3, 4.4, 5.5, 6.6};
    orig.elements.push_back(elem);

    auto pd = write_element_results_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_element_results_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->gnote.value == 9);
    CHECK(r->scn == 2);
    CHECK_THAT(r->time, WithinRel(25.5));
    CHECK(r->nv == 3);
    CHECK(r->rrf == 0);
    CHECK(r->ne == 1);

    REQUIRE(r->elements.size() == 1);
    auto const& re = r->elements[0];
    CHECK(re.en == 42);
    CHECK(re.ep.value == 11);
    CHECK(re.itop == 5);
    CHECK(re.nl == 1);
    CHECK(re.dlf == 0);
    CHECK(re.nrl == 2);
    REQUIRE(re.rdrl.size() == 2);
    CHECK(re.rdrl[0] == 3);
    CHECK(re.rdrl[1] == 7);
    CHECK(re.numv == 6);
    REQUIRE(re.values.size() == 6);
    for (int i = 0; i < 6; ++i) {
        CHECK_THAT(re.values[i], WithinRel(elem.values[i]));
    }
}
