// Tests for §4.70 — Line Font Definition Entity (Type 304).
// Spec reference: IGES 5.3, §4.70, pages 292-295.

#include <catch2/catch_test_macros.hpp>
#include "entities/line_font_definition_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.70 Form 1: Template subfigure — M (display flag), L1, L2, L3
// -----------------------------------------------------------------

TEST_CASE("§4.70 — Form 1: parse template subfigure line font", "[entity][spec-4.70]") {
    // §4.70 Form 1: M=0 (align with axes), L1=DE 5, L2=2.5, L3=0.5
    ParamTokenizer tok("0,5,2.5,0.5;", ',', ';');
    auto r = parse_line_font_definition_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->form == 1);
    CHECK(r->m == 0);
    CHECK(r->l1.value == 5);
    CHECK(r->l2 == 2.5);
    CHECK(r->l3 == 0.5);
}

TEST_CASE("§4.70 — Form 1: display flag = 1 (tangent alignment)", "[entity][spec-4.70]") {
    ParamTokenizer tok("1,7,3.0,1.0;", ',', ';');
    auto r = parse_line_font_definition_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->m == 1);
    CHECK(r->l1.value == 7);
    CHECK(r->l2 == 3.0);
    CHECK(r->l3 == 1.0);
}

// -----------------------------------------------------------------
// §4.70 Form 2: Visible-blank pattern — M, L(1)..L(M), B
// -----------------------------------------------------------------

TEST_CASE("§4.70 — Form 2: parse visible-blank pattern", "[entity][spec-4.70]") {
    // §4.70 Form 2: M=5, 5 segment lengths, B="16" (hex for bit pattern 10110)
    ParamTokenizer tok("5,2.0,1.0,2.0,2.0,2.0,2H16;", ',', ';');
    auto r = parse_line_font_definition_entity(tok, 2);
    REQUIRE(r.has_value());
    CHECK(r->form == 2);
    CHECK(r->m == 5);
    REQUIRE(r->segments.size() == 5);
    CHECK(r->segments[0] == 2.0);
    CHECK(r->segments[1] == 1.0);
    CHECK(r->bitmask == "16");
}

TEST_CASE("§4.70 — Form 2: 3-segment dash-dot pattern", "[entity][spec-4.70]") {
    // M=3, segments: 2.0 (visible), 0.5 (blank), 0.5 (visible)
    // B="5" → binary 101 → segments 1 and 3 visible
    ParamTokenizer tok("3,2.0,0.5,0.5,1H5;", ',', ';');
    auto r = parse_line_font_definition_entity(tok, 2);
    REQUIRE(r.has_value());
    CHECK(r->m == 3);
    REQUIRE(r->segments.size() == 3);
    CHECK(r->bitmask == "5");
}

// -----------------------------------------------------------------
// Round-trip: Form 1
// -----------------------------------------------------------------

TEST_CASE("§4.70 — round-trip Form 1", "[entity][spec-4.70]") {
    LineFontDefinitionEntity orig;
    orig.form = 1;
    orig.m = 0;
    orig.l1 = DEIndex{5};
    orig.l2 = 2.5;
    orig.l3 = 0.5;

    auto pd = write_line_font_definition_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_line_font_definition_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->m == 0);
    CHECK(r->l1.value == 5);
    CHECK(r->l2 == 2.5);
    CHECK(r->l3 == 0.5);
}

// -----------------------------------------------------------------
// Round-trip: Form 2
// -----------------------------------------------------------------

TEST_CASE("§4.70 — round-trip Form 2", "[entity][spec-4.70]") {
    LineFontDefinitionEntity orig;
    orig.form = 2;
    orig.m = 3;
    orig.segments = {2.0, 0.5, 0.5};
    orig.bitmask = "5";

    auto pd = write_line_font_definition_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_line_font_definition_entity(tok, 2);
    REQUIRE(r.has_value());
    CHECK(r->m == 3);
    REQUIRE(r->segments.size() == 3);
    CHECK(r->segments[0] == 2.0);
    CHECK(r->bitmask == "5");
}
