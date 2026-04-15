// Tests for §4.56 — Curve Dimension Entity (Type 204).
// Spec reference: IGES 5.3, §4.56, page 262.

#include <catch2/catch_test_macros.hpp>
#include "entities/curve_dimension_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.56: "Parameters: DENOTE, DECURV1, DECURV2, DEARR1, DEARR2,
//   DEWIT1, DEWIT2" (7 pointers)
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.56 — parse curve dimension entity (7 pointers)", "[entity][spec-4.56]") {
    // §4.56 PD: "Index 1: DENOTE, 2: DECURV1, 3: DECURV2,
    //   4: DEARR1, 5: DEARR2, 6: DEWIT1, 7: DEWIT2"
    ParamTokenizer tok("1,3,5,7,9,11,13;", ',', ';');
    auto r = parse_curve_dimension_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == 1);
    CHECK(r->decurv1.value == 3);
    CHECK(r->decurv2.value == 5);
    CHECK(r->dearr1.value == 7);
    CHECK(r->dearr2.value == 9);
    CHECK(r->dewit1.value == 11);
    CHECK(r->dewit2.value == 13);
}

// ─────────────────────────────────────────────────────────────────
// §4.56: All 7 fields are pointers to DE entries
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.56 — all fields are DE pointers", "[entity][spec-4.56]") {
    // §4.56: Each field is a "Pointer to the DE" of various entities
    CurveDimensionEntity e;
    e.denote = DEIndex{101};
    e.decurv1 = DEIndex{103};
    e.decurv2 = DEIndex{105};
    e.dearr1 = DEIndex{107};
    e.dearr2 = DEIndex{109};
    e.dewit1 = DEIndex{111};
    e.dewit2 = DEIndex{113};

    auto pd = write_curve_dimension_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_curve_dimension_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == 101);
    CHECK(r->dewit2.value == 113);
}

// ─────────────────────────────────────────────────────────────────
// Round-trip: write then parse
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.56 — round-trip curve dimension entity", "[entity][spec-4.56]") {
    CurveDimensionEntity orig;
    orig.denote = DEIndex{21};
    orig.decurv1 = DEIndex{23};
    orig.decurv2 = DEIndex{25};
    orig.dearr1 = DEIndex{27};
    orig.dearr2 = DEIndex{29};
    orig.dewit1 = DEIndex{31};
    orig.dewit2 = DEIndex{33};

    auto pd = write_curve_dimension_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_curve_dimension_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == orig.denote.value);
    CHECK(r->decurv1.value == orig.decurv1.value);
    CHECK(r->decurv2.value == orig.decurv2.value);
    CHECK(r->dearr1.value == orig.dearr1.value);
    CHECK(r->dearr2.value == orig.dearr2.value);
    CHECK(r->dewit1.value == orig.dewit1.value);
    CHECK(r->dewit2.value == orig.dewit2.value);
}
