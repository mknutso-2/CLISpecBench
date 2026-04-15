// Tests for §4.77 — Units Data Entity (Type 316).
// Spec reference: IGES 5.3, §4.77, page 332.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/units_data_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;

// -----------------------------------------------------------------
// §4.77: "Parameters: NP, {TYP, VAL, SF} repeated NP times"
// -----------------------------------------------------------------

TEST_CASE("§4.77 — parse units data with one unit", "[entity][spec-4.77]") {
    // §4.77 PD: "Index 1: NP, then per unit: TYP(String), VAL(String), SF(Real)"
    ParamTokenizer tok("1,6HLENGTH,2HMM,1.0;", ',', ';');
    auto r = parse_units_data_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->np == 1);
    CHECK(r->units.size() == 1);
    CHECK(r->units[0].typ == "LENGTH");
    CHECK(r->units[0].val == "MM");
    CHECK_THAT(r->units[0].sf, WithinRel(1.0));
}

// -----------------------------------------------------------------
// §4.77: Multiple unit entries
// -----------------------------------------------------------------

TEST_CASE("§4.77 — parse units data with multiple units", "[entity][spec-4.77]") {
    // §4.77: NP unit triples (TYP, VAL, SF)
    ParamTokenizer tok("2,6HLENGTH,2HIN,25.4,4HMASS,2HKG,1.0;", ',', ';');
    auto r = parse_units_data_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->np == 2);
    CHECK(r->units.size() == 2);
    CHECK(r->units[0].typ == "LENGTH");
    CHECK(r->units[0].val == "IN");
    CHECK_THAT(r->units[0].sf, WithinRel(25.4));
    CHECK(r->units[1].typ == "MASS");
    CHECK(r->units[1].val == "KG");
    CHECK_THAT(r->units[1].sf, WithinRel(1.0));
}

// -----------------------------------------------------------------
// §4.77: Scale factor preserved
// -----------------------------------------------------------------

TEST_CASE("§4.77 — scale factor preserved", "[entity][spec-4.77]") {
    // §4.77: "SF: Scale factor to convert units to SI"
    UnitsDataEntity e;
    e.np = 1;
    e.units = {{.typ = "LENGTH", .val = "FT", .sf = 304.8}};

    auto pd = write_units_data_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_units_data_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->units[0].sf, WithinRel(304.8));
}

// -----------------------------------------------------------------
// Round-trip: write then parse
// -----------------------------------------------------------------

TEST_CASE("§4.77 — round-trip units data entity", "[entity][spec-4.77]") {
    UnitsDataEntity orig;
    orig.np = 3;
    orig.units = {
        {.typ = "LENGTH", .val = "MM", .sf = 1.0},
        {.typ = "MASS", .val = "G", .sf = 0.001},
        {.typ = "TIME", .val = "S", .sf = 1.0},
    };

    auto pd = write_units_data_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_units_data_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->np == 3);
    CHECK(r->units.size() == 3);
    CHECK(r->units[0].typ == "LENGTH");
    CHECK(r->units[0].val == "MM");
    CHECK_THAT(r->units[0].sf, WithinRel(1.0));
    CHECK(r->units[1].typ == "MASS");
    CHECK(r->units[1].val == "G");
    CHECK_THAT(r->units[1].sf, WithinRel(0.001));
    CHECK(r->units[2].typ == "TIME");
    CHECK(r->units[2].val == "S");
    CHECK_THAT(r->units[2].sf, WithinRel(1.0));
}
