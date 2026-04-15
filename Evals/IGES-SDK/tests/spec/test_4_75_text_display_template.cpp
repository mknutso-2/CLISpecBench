// Tests for §4.75 — Text Display Template Entity (Type 312).
// Spec reference: IGES 5.3, §4.75, pages 328-329.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/text_display_template_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// -----------------------------------------------------------------
// §4.75: "Parameters: CBW, CBH, FC, SL, A, M, VH, XS, YS, ZS"
// (10 parameters, same structure for Forms 0 and 1)
// -----------------------------------------------------------------

TEST_CASE("§4.75 — parse text display template (10 params)", "[entity][spec-4.75]") {
    // §4.75 PD: "Index 1: CBW, 2: CBH, 3: FC, 4: SL, 5: A,
    //   6: M, 7: VH, 8: XS, 9: YS, 10: ZS"
    ParamTokenizer tok("0.2,0.3,1,1.5708,0.0,0,0,1.0,2.0,0.0;", ',', ';');
    auto r = parse_text_display_template_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->cbw, WithinRel(0.2));
    CHECK_THAT(r->cbh, WithinRel(0.3));
    CHECK(r->fc == 1);
    CHECK_THAT(r->sl, WithinRel(1.5708));
    CHECK_THAT(r->a, WithinAbs(0.0, 1e-15));
    CHECK(r->m == 0);
    CHECK(r->vh == 0);
    CHECK_THAT(r->xs, WithinRel(1.0));
    CHECK_THAT(r->ys, WithinRel(2.0));
    CHECK_THAT(r->zs, WithinAbs(0.0, 1e-15));
}

// -----------------------------------------------------------------
// §4.75: "M: Mirror flag" (0, 1, or 2)
// -----------------------------------------------------------------

TEST_CASE("§4.75 — mirror flag values preserved", "[entity][spec-4.75]") {
    // §4.75: "M: 0=no mirroring, 1=mirror about axis perpendicular
    //   to text base line, 2=mirror about text base line"
    TextDisplayTemplateEntity e;
    e.cbw = 0.1; e.cbh = 0.2;
    e.fc = 1; e.sl = 1.5708; e.a = 0.0;
    e.m = 2;
    e.vh = 0;
    e.xs = 0.0; e.ys = 0.0; e.zs = 0.0;

    auto pd = write_text_display_template_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_text_display_template_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->m == 2);
}

// -----------------------------------------------------------------
// §4.75: "VH: 0=text is horizontal, 1=text is vertical"
// -----------------------------------------------------------------

TEST_CASE("§4.75 — vertical text flag", "[entity][spec-4.75]") {
    // §4.75: "VH: Rotate internal text flag"
    TextDisplayTemplateEntity e;
    e.cbw = 0.1; e.cbh = 0.2;
    e.fc = 1; e.sl = 1.5708; e.a = 0.0;
    e.m = 0; e.vh = 1;
    e.xs = 0.0; e.ys = 0.0; e.zs = 0.0;

    auto pd = write_text_display_template_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_text_display_template_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->vh == 1);
}

// -----------------------------------------------------------------
// §4.75: Negative FC indicates pointer to Text Font Definition
// -----------------------------------------------------------------

TEST_CASE("§4.75 — negative FC is pointer to font definition", "[entity][spec-4.75]") {
    // §4.75: "FC: Font code ... negative value is a pointer to
    //   a Text Font Definition Entity"
    TextDisplayTemplateEntity e;
    e.cbw = 0.5; e.cbh = 0.8;
    e.fc = -7;
    e.sl = 1.5708; e.a = 0.0;
    e.m = 0; e.vh = 0;
    e.xs = 5.0; e.ys = 10.0; e.zs = 0.0;

    auto pd = write_text_display_template_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_text_display_template_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->fc == -7);
}

// -----------------------------------------------------------------
// Round-trip: write then parse
// -----------------------------------------------------------------

TEST_CASE("§4.75 — round-trip text display template", "[entity][spec-4.75]") {
    TextDisplayTemplateEntity orig;
    orig.cbw = 0.25; orig.cbh = 0.35;
    orig.fc = 3;
    orig.sl = 1.2; orig.a = 0.785;
    orig.m = 1; orig.vh = 0;
    orig.xs = 100.0; orig.ys = 200.0; orig.zs = 50.0;

    auto pd = write_text_display_template_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_text_display_template_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->cbw, WithinRel(orig.cbw));
    CHECK_THAT(r->cbh, WithinRel(orig.cbh));
    CHECK(r->fc == orig.fc);
    CHECK_THAT(r->sl, WithinRel(orig.sl));
    CHECK_THAT(r->a, WithinRel(orig.a));
    CHECK(r->m == orig.m);
    CHECK(r->vh == orig.vh);
    CHECK_THAT(r->xs, WithinRel(orig.xs));
    CHECK_THAT(r->ys, WithinRel(orig.ys));
    CHECK_THAT(r->zs, WithinRel(orig.zs));
}
