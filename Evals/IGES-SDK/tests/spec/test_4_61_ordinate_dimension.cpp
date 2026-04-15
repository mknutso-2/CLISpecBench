// Tests for §4.64 — Ordinate Dimension Entity (Type 218).
// Spec reference: IGES 5.3, §4.64, pages 264-265.

#include <catch2/catch_test_macros.hpp>
#include "entities/ordinate_dimension_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.64 Form 0 PD table (page 265): DENOTE, DEWIT
// §4.64 Form 1 PD table (page 265): DENOTE, DEORD, DESUPP
// -----------------------------------------------------------------

TEST_CASE("§4.64 — parse ordinate dimension Form 0", "[entity][spec-4.64]") {
    // Form 0: 2 fields — DENOTE, DEWIT
    ParamTokenizer tok("1,3;", ',', ';');
    auto r = parse_ordinate_dimension_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == 1);
    CHECK(r->dewit.value == 3);
}

TEST_CASE("§4.64 — Form 0 with null witness line", "[entity][spec-4.64]") {
    ParamTokenizer tok("1,0;", ',', ';');
    auto r = parse_ordinate_dimension_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r->dewit.is_null());
}

TEST_CASE("§4.64 — parse ordinate dimension Form 1", "[entity][spec-4.64]") {
    // Form 1: 3 fields — DENOTE, DEORD, DESUPP
    ParamTokenizer tok("1,3,5;", ',', ';');
    auto r = parse_ordinate_dimension_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == 1);
    CHECK(r->deord.value == 3);
    CHECK(r->desupp.value == 5);
}

TEST_CASE("§4.64 — round-trip ordinate dimension Form 0", "[entity][spec-4.64]") {
    OrdinateDimensionEntity orig;
    orig.form = 0;
    orig.denote = DEIndex{1};
    orig.dewit = DEIndex{3};

    auto pd = write_ordinate_dimension_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_ordinate_dimension_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == 1);
    CHECK(r->dewit.value == 3);
}

TEST_CASE("§4.64 — round-trip ordinate dimension Form 1", "[entity][spec-4.64]") {
    OrdinateDimensionEntity orig;
    orig.form = 1;
    orig.denote = DEIndex{1};
    orig.deord = DEIndex{3};
    orig.desupp = DEIndex{5};

    auto pd = write_ordinate_dimension_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_ordinate_dimension_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == 1);
    CHECK(r->deord.value == 3);
    CHECK(r->desupp.value == 5);
}
