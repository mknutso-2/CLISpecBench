// Tests for §4.66 — Radius Dimension Entity (Type 222).
// Spec reference: IGES 5.3, §4.66, pages 269-270.

#include <catch2/catch_test_macros.hpp>
#include "entities/radius_dimension_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.66 Form 0 PD table (page 270): DENOTE, DEARRW, XT, YT
// §4.66 Form 1 PD table (page 270): DENOTE, DEARRW, XT, YT, DEARRW2
// -----------------------------------------------------------------

TEST_CASE("§4.66 — parse radius dimension Form 0", "[entity][spec-4.66]") {
    ParamTokenizer tok("1,3,10.0,20.0;", ',', ';');
    auto r = parse_radius_dimension_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == 1);
    CHECK(r->dearrw.value == 3);
    CHECK(r->xt == 10.0);
    CHECK(r->yt == 20.0);
}

TEST_CASE("§4.66 — parse radius dimension Form 1", "[entity][spec-4.66]") {
    // Form 1 adds DEARRW2 (5th field)
    ParamTokenizer tok("1,3,10.0,20.0,7;", ',', ';');
    auto r = parse_radius_dimension_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == 1);
    CHECK(r->dearrw.value == 3);
    CHECK(r->xt == 10.0);
    CHECK(r->yt == 20.0);
    CHECK(r->dearrw2.value == 7);
}

TEST_CASE("§4.66 — round-trip radius dimension Form 0", "[entity][spec-4.66]") {
    RadiusDimensionEntity orig;
    orig.form = 0;
    orig.denote = DEIndex{1};
    orig.dearrw = DEIndex{3};
    orig.xt = 10.0;
    orig.yt = 20.0;

    auto pd = write_radius_dimension_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_radius_dimension_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == 1);
    CHECK(r->dearrw.value == 3);
    CHECK(r->xt == 10.0);
    CHECK(r->yt == 20.0);
}

TEST_CASE("§4.66 — round-trip radius dimension Form 1", "[entity][spec-4.66]") {
    RadiusDimensionEntity orig;
    orig.form = 1;
    orig.denote = DEIndex{1};
    orig.dearrw = DEIndex{3};
    orig.xt = 10.0;
    orig.yt = 20.0;
    orig.dearrw2 = DEIndex{7};

    auto pd = write_radius_dimension_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_radius_dimension_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == 1);
    CHECK(r->dearrw.value == 3);
    CHECK(r->xt == 10.0);
    CHECK(r->yt == 20.0);
    CHECK(r->dearrw2.value == 7);
}
