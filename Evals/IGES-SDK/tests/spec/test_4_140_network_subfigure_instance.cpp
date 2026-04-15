// Tests for §4.140 — Network Subfigure Instance Entity (Type 420).
// Spec reference: IGES 5.3, §4.140, pages 508-509.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/network_subfigure_instance_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;

// -----------------------------------------------------------------
// §4.140: "Parameters: DE, X, Y, Z, XS, YS, ZS, TF, PRD, DPTR,
//   NC, CPTR(1..NC)"
// -----------------------------------------------------------------

TEST_CASE("§4.140 — parse network subfigure instance", "[entity][spec-4.140]") {
    // §4.140 PD: DE=1, X=10.0, Y=20.0, Z=0.0, XS=1.0, YS=1.0, ZS=1.0,
    //   TF=2 (physical), PRD="U1", DPTR=3, NC=2, CPTR(1)=5, CPTR(2)=7
    ParamTokenizer tok("1,10.0,20.0,0.0,1.0,1.0,1.0,2,2HU1,3,2,5,7;", ',', ';');
    auto r = parse_network_subfigure_instance_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->de.value == 1);
    CHECK_THAT(r->x, WithinRel(10.0));
    CHECK_THAT(r->y, WithinRel(20.0));
    CHECK_THAT(r->z, WithinRel(0.0));
    CHECK_THAT(r->xs, WithinRel(1.0));
    CHECK_THAT(r->ys, WithinRel(1.0));
    CHECK_THAT(r->zs, WithinRel(1.0));
    CHECK(r->tf == 2);
    CHECK(r->prd == "U1");
    CHECK(r->dptr.value == 3);
    CHECK(r->nc == 2);
    REQUIRE(r->cptrs.size() == 2);
    CHECK(r->cptrs[0].value == 5);
    CHECK(r->cptrs[1].value == 7);
}

// -----------------------------------------------------------------
// §4.140: "any unused points of connection ... indicated by a null
//   (zero) pointer"
// -----------------------------------------------------------------

TEST_CASE("§4.140 — null connect point pointers", "[entity][spec-4.140]") {
    NetworkSubfigureInstanceEntity e;
    e.de = DEIndex{1};
    e.x = 5.0; e.y = 10.0; e.z = 0.0;
    e.xs = 2.0; e.ys = 2.0; e.zs = 2.0;
    e.tf = 1;
    e.prd = "R1";
    e.dptr = DEIndex{0};
    e.nc = 3;
    e.cptrs = {DEIndex{5}, DEIndex{0}, DEIndex{9}};

    auto pd = write_network_subfigure_instance_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_network_subfigure_instance_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->cptrs[0].value == 5);
    CHECK(r->cptrs[1].value == 0);
    CHECK(r->cptrs[2].value == 9);
}

// -----------------------------------------------------------------
// §4.140: "Type Flag Field (Index 8) implements the distinction
//   between logical design and physical design data"
// -----------------------------------------------------------------

TEST_CASE("§4.140 — type flag values", "[entity][spec-4.140]") {
    NetworkSubfigureInstanceEntity e;
    e.de = DEIndex{1};
    e.x = 0.0; e.y = 0.0; e.z = 0.0;
    e.xs = 1.0; e.ys = 1.0; e.zs = 1.0;
    e.tf = 0;
    e.prd = "J1";
    e.dptr = DEIndex{0};
    e.nc = 0;

    auto pd = write_network_subfigure_instance_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_network_subfigure_instance_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->tf == 0);
    CHECK(r->nc == 0);
    CHECK(r->cptrs.empty());
}

// -----------------------------------------------------------------
// Round-trip: write then parse
// -----------------------------------------------------------------

TEST_CASE("§4.140 — round-trip network subfigure instance", "[entity][spec-4.140]") {
    NetworkSubfigureInstanceEntity orig;
    orig.de = DEIndex{11};
    orig.x = -5.5; orig.y = 12.3; orig.z = 0.1;
    orig.xs = 0.5; orig.ys = 0.5; orig.zs = 0.5;
    orig.tf = 2;
    orig.prd = "IC3";
    orig.dptr = DEIndex{15};
    orig.nc = 1;
    orig.cptrs = {DEIndex{17}};

    auto pd = write_network_subfigure_instance_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_network_subfigure_instance_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->de.value == 11);
    CHECK_THAT(r->x, WithinRel(-5.5));
    CHECK_THAT(r->y, WithinRel(12.3));
    CHECK_THAT(r->z, WithinRel(0.1));
    CHECK_THAT(r->xs, WithinRel(0.5));
    CHECK(r->tf == 2);
    CHECK(r->prd == "IC3");
    CHECK(r->dptr.value == 15);
    CHECK(r->cptrs[0].value == 17);
}
