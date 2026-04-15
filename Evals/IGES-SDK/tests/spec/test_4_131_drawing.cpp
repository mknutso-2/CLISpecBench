// Tests for §4.96 — Drawing Entity (Type 404).
// Spec reference: IGES 5.3, §4.96, pages 409-412.

#include <catch2/catch_test_macros.hpp>
#include "entities/drawing_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.96 Form 0: per-view fields are VPTR, XORIGIN, YORIGIN
// -----------------------------------------------------------------

TEST_CASE("§4.96 — parse Form 0 drawing with 1 view, no annotations", "[entity][spec-4.96]") {
    ParamTokenizer tok("1,3,0.0,0.0,0;", ',', ';');
    auto r = parse_drawing_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r->n == 1);
    REQUIRE(r->views.size() == 1);
    CHECK(r->views[0].view.value == 3);
    CHECK(r->views[0].x_origin == 0.0);
    CHECK(r->views[0].y_origin == 0.0);
    CHECK(r->m == 0);
    CHECK(r->annotations.empty());
}

TEST_CASE("§4.96 — parse Form 0 drawing with 2 views and 1 annotation", "[entity][spec-4.96]") {
    ParamTokenizer tok("2,3,10.0,20.0,5,30.0,40.0,1,7;", ',', ';');
    auto r = parse_drawing_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r->n == 2);
    REQUIRE(r->views.size() == 2);
    CHECK(r->views[0].view.value == 3);
    CHECK(r->views[0].x_origin == 10.0);
    CHECK(r->views[1].view.value == 5);
    CHECK(r->views[1].y_origin == 40.0);
    CHECK(r->m == 1);
    REQUIRE(r->annotations.size() == 1);
    CHECK(r->annotations[0].value == 7);
}

// -----------------------------------------------------------------
// §4.96 Form 1: per-view fields are VPTR, XORIGIN, YORIGIN, ANGLE
// -----------------------------------------------------------------

TEST_CASE("§4.96 — parse Form 1 drawing with angle", "[entity][spec-4.96]") {
    // §4.96 Form 1: ANGLE(i) is orientation angle in radians
    ParamTokenizer tok("1,3,10.0,20.0,1.5708,0;", ',', ';');
    auto r = parse_drawing_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->n == 1);
    REQUIRE(r->views.size() == 1);
    CHECK(r->views[0].view.value == 3);
    CHECK(r->views[0].x_origin == 10.0);
    CHECK(r->views[0].y_origin == 20.0);
    CHECK(r->views[0].angle == 1.5708);
    CHECK(r->m == 0);
}

TEST_CASE("§4.96 — parse Form 1 with 2 views and annotations", "[entity][spec-4.96]") {
    ParamTokenizer tok("2,1,0.0,0.0,0.0,3,5.0,10.0,3.14159,2,7,9;", ',', ';');
    auto r = parse_drawing_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->n == 2);
    CHECK(r->views[0].angle == 0.0);
    CHECK(r->views[1].angle == 3.14159);
    CHECK(r->m == 2);
    CHECK(r->annotations[0].value == 7);
    CHECK(r->annotations[1].value == 9);
}

// -----------------------------------------------------------------
// Round-trip: Form 0
// -----------------------------------------------------------------

TEST_CASE("§4.96 — round-trip Form 0", "[entity][spec-4.96]") {
    DrawingEntity orig;
    orig.n = 1;
    orig.views.push_back({DEIndex{3}, 10.0, 20.0, 0.0});
    orig.m = 1;
    orig.annotations.push_back(DEIndex{7});

    auto pd = write_drawing_entity(orig, 0);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_drawing_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r->views[0].view.value == 3);
    CHECK(r->views[0].x_origin == 10.0);
    CHECK(r->views[0].y_origin == 20.0);
    CHECK(r->annotations[0].value == 7);
}

// -----------------------------------------------------------------
// Round-trip: Form 1
// -----------------------------------------------------------------

TEST_CASE("§4.96 — round-trip Form 1", "[entity][spec-4.96]") {
    DrawingEntity orig;
    orig.n = 2;
    orig.views.push_back({DEIndex{1}, 0.0, 0.0, 0.0});
    orig.views.push_back({DEIndex{3}, 5.0, 10.0, 1.5708});
    orig.m = 1;
    orig.annotations.push_back(DEIndex{9});

    auto pd = write_drawing_entity(orig, 1);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_drawing_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->n == 2);
    CHECK(r->views[0].angle == 0.0);
    CHECK(r->views[1].angle == 1.5708);
    CHECK(r->views[1].x_origin == 5.0);
    CHECK(r->annotations[0].value == 9);
}
