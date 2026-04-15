// Tests for §4.62 — Leader (Arrow) Entity (Type 214).
// Spec reference: IGES 5.3, §4.62, pages 257-261.

#include <catch2/catch_test_macros.hpp>
#include "entities/leader_arrow_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.62 PD table (page 259): N, AD1, AD2, ZT, XH, YH, then
//   per-segment: X(i), Y(i). Arrowhead style via DE Form Number.
// -----------------------------------------------------------------

TEST_CASE("§4.62 — parse leader arrow with 1 segment", "[entity][spec-4.62]") {
    // §4.62: N=1, AD1=0.5, AD2=0.25, ZT=0.0, XH=1.0, YH=2.0, X(1)=5.0, Y(1)=2.0
    ParamTokenizer tok("1,0.5,0.25,0.0,1.0,2.0,5.0,2.0;", ',', ';');
    auto r = parse_leader_arrow_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->n == 1);
    CHECK(r->ad1 == 0.5);
    CHECK(r->ad2 == 0.25);
    CHECK(r->zt == 0.0);
    CHECK(r->xh == 1.0);
    CHECK(r->yh == 2.0);
    REQUIRE(r->segments.size() == 1);
    CHECK(r->segments[0].x == 5.0);
    CHECK(r->segments[0].y == 2.0);
}

TEST_CASE("§4.62 — parse leader arrow with 2 segments", "[entity][spec-4.62]") {
    // §4.62: N=2, AD1=1.0, AD2=0.5, ZT=0.0, XH=0.0, YH=0.0,
    //        X(1)=3.0, Y(1)=0.0, X(2)=3.0, Y(2)=5.0
    ParamTokenizer tok("2,1.0,0.5,0.0,0.0,0.0,3.0,0.0,3.0,5.0;", ',', ';');
    auto r = parse_leader_arrow_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->n == 2);
    CHECK(r->ad1 == 1.0);
    CHECK(r->ad2 == 0.5);
    REQUIRE(r->segments.size() == 2);
    CHECK(r->segments[0].x == 3.0);
    CHECK(r->segments[0].y == 0.0);
    CHECK(r->segments[1].x == 3.0);
    CHECK(r->segments[1].y == 5.0);
}

TEST_CASE("§4.62 — parse leader with non-zero Z depth", "[entity][spec-4.62]") {
    // §4.62: ZT is the Z depth from the XT,YT plane
    ParamTokenizer tok("1,0.3,0.15,5.0,10.0,20.0,15.0,20.0;", ',', ';');
    auto r = parse_leader_arrow_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->zt == 5.0);
    CHECK(r->xh == 10.0);
    CHECK(r->yh == 20.0);
}

TEST_CASE("§4.62 — round-trip leader arrow", "[entity][spec-4.62]") {
    LeaderArrowEntity orig;
    orig.n = 3;
    orig.ad1 = 0.8;
    orig.ad2 = 0.4;
    orig.zt = 1.5;
    orig.xh = 10.0;
    orig.yh = 20.0;
    orig.segments = {{5.0, 10.0}, {5.0, 15.0}, {8.0, 15.0}};

    auto pd = write_leader_arrow_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_leader_arrow_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->n == 3);
    CHECK(r->ad1 == 0.8);
    CHECK(r->ad2 == 0.4);
    CHECK(r->zt == 1.5);
    CHECK(r->xh == 10.0);
    CHECK(r->yh == 20.0);
    REQUIRE(r->segments.size() == 3);
    CHECK(r->segments[0].x == 5.0);
    CHECK(r->segments[0].y == 10.0);
    CHECK(r->segments[2].x == 8.0);
    CHECK(r->segments[2].y == 15.0);
}
