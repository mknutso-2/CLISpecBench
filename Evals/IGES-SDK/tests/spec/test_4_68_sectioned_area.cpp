// Tests for §4.68 — Sectioned Area Entity (Type 230).
// Spec reference: IGES 5.3, §4.68, pages 275-279.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/sectioned_area_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"
using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// ─────────────────────────────────────────────────────────────────
// §4.68: "Parameters: BNDP, PATRN, XT, YT, ZT, DIST, ANGLE, N,
//   ISLPT(1)..ISLPT(N)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.68 — parse sectioned area entity", "[entity][spec-4.68]") {
    // §4.68 PD: "Index 1: BNDP, 2: PATRN, 3: XT, 4: YT, 5: ZT,
    //   6: DIST, 7: ANGLE, 8: N, 9..8+N: ISLPT(i)"
    ParamTokenizer tok("5,2,1.0,2.0,0.0,0.5,0.785,1,7;", ',', ';');
    auto r = parse_sectioned_area_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->bndp.value == 5);
    CHECK(r->patrn == 2);
    CHECK_THAT(r->xt, WithinRel(1.0));
    CHECK_THAT(r->yt, WithinRel(2.0));
    CHECK_THAT(r->zt, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r->dist, WithinRel(0.5));
    CHECK_THAT(r->angle, WithinRel(0.785));
    CHECK(r->n == 1);
    CHECK(r->islands.size() == 1);
    CHECK(r->islands[0].value == 7);
}

// ─────────────────────────────────────────────────────────────────
// §4.68: "PATRN: Fill pattern code" (0-19 standard)
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.68 — fill pattern code preserved", "[entity][spec-4.68]") {
    // §4.68: "PATRN: Fill pattern code" — Table 10 lists codes 0-19
    SectionedAreaEntity e;
    e.bndp = DEIndex{1};
    e.patrn = 19;  // Solid fill
    e.dist = 1.0; e.angle = 0.0;

    auto pd = write_sectioned_area_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_sectioned_area_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->patrn == 19);
}

// ─────────────────────────────────────────────────────────────────
// §4.68: Sectioned area with no islands (N=0)
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.68 — sectioned area with no islands", "[entity][spec-4.68]") {
    // §4.68: "N: Number of island curves or zero"
    ParamTokenizer tok("3,1,0.0,0.0,0.0,1.0,0.785,0;", ',', ';');
    auto r = parse_sectioned_area_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->n == 0);
    CHECK(r->islands.empty());
}

// ─────────────────────────────────────────────────────────────────
// §4.68: "ANGLE ... Default = pi/4, measured in radians"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.68 — angle parameter in radians", "[entity][spec-4.68]") {
    // §4.68: "ANGLE: Angle measured in radians from the XT axis"
    SectionedAreaEntity e;
    e.bndp = DEIndex{1};
    e.patrn = 0;
    e.angle = 3.14159265358979323846 / 4.0;  // default angle per spec
    e.dist = 2.0;

    auto pd = write_sectioned_area_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_sectioned_area_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->angle, WithinRel(3.14159265358979323846 / 4.0));
}

// ─────────────────────────────────────────────────────────────────
// §4.68: Sectioned area with multiple islands
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.68 — sectioned area with multiple islands", "[entity][spec-4.68]") {
    // §4.68: N island definition curves
    SectionedAreaEntity e;
    e.bndp = DEIndex{1};
    e.patrn = 1;
    e.dist = 1.0; e.angle = 0.0;
    e.n = 3;
    e.islands = {DEIndex{11}, DEIndex{13}, DEIndex{15}};

    auto pd = write_sectioned_area_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_sectioned_area_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->n == 3);
    CHECK(r->islands.size() == 3);
    CHECK(r->islands[0].value == 11);
    CHECK(r->islands[1].value == 13);
    CHECK(r->islands[2].value == 15);
}

// ─────────────────────────────────────────────────────────────────
// Round-trip: write then parse
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.68 — round-trip sectioned area entity", "[entity][spec-4.68]") {
    SectionedAreaEntity orig;
    orig.bndp = DEIndex{21};
    orig.patrn = 5;
    orig.xt = 10.0; orig.yt = 20.0; orig.zt = 0.0;
    orig.dist = 3.5;
    orig.angle = 1.047;
    orig.n = 2;
    orig.islands = {DEIndex{23}, DEIndex{25}};

    auto pd = write_sectioned_area_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_sectioned_area_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->bndp.value == orig.bndp.value);
    CHECK(r->patrn == orig.patrn);
    CHECK_THAT(r->xt, WithinRel(orig.xt));
    CHECK_THAT(r->yt, WithinRel(orig.yt));
    CHECK_THAT(r->zt, WithinAbs(orig.zt, 1e-15));
    CHECK_THAT(r->dist, WithinRel(orig.dist));
    CHECK_THAT(r->angle, WithinRel(orig.angle));
    CHECK(r->n == orig.n);
    CHECK(r->islands[0].value == 23);
    CHECK(r->islands[1].value == 25);
}
