// Tests for §4.65 — Point Dimension Entity (Type 220).
// Spec reference: IGES 5.3, §4.65, page 273.

#include <catch2/catch_test_macros.hpp>
#include "entities/point_dimension_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.65: "Parameters: DENOTE, DEARRW, DEGEOM" (3 pointers)
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.65 — parse point dimension entity (3 pointers)", "[entity][spec-4.65]") {
    // §4.65 PD: "Index 1: DENOTE, 2: DEARRW, 3: DEGEOM"
    ParamTokenizer tok("1,3,5;", ',', ';');
    auto r = parse_point_dimension_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == 1);
    CHECK(r->dearrw.value == 3);
    CHECK(r->degeom.value == 5);
}

// ─────────────────────────────────────────────────────────────────
// §4.65: All fields are pointers to DE entries
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.65 — all fields are DE pointers", "[entity][spec-4.65]") {
    // §4.65: DENOTE -> General Note, DEARRW -> leader, DEGEOM -> geometry
    PointDimensionEntity e;
    e.denote = DEIndex{201};
    e.dearrw = DEIndex{203};
    e.degeom = DEIndex{205};

    auto pd = write_point_dimension_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_point_dimension_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == 201);
    CHECK(r->dearrw.value == 203);
    CHECK(r->degeom.value == 205);
}

// ─────────────────────────────────────────────────────────────────
// Round-trip: write then parse
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.65 — round-trip point dimension entity", "[entity][spec-4.65]") {
    PointDimensionEntity orig;
    orig.denote = DEIndex{51};
    orig.dearrw = DEIndex{53};
    orig.degeom = DEIndex{55};

    auto pd = write_point_dimension_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_point_dimension_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == orig.denote.value);
    CHECK(r->dearrw.value == orig.dearrw.value);
    CHECK(r->degeom.value == orig.degeom.value);
}
