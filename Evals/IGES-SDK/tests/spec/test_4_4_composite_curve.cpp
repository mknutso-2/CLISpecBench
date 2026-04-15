// Tests for §4.4 — Composite Curve Entity (Type 102).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/composite_curve_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.4: "A composite curve is defined as an ordered list of
//   entities ... each of which is independently defined"
//   Parameters: N (count), DE1, DE2, ..., DEN (pointers)
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.4 — parse composite curve with 3 constituents", "[entity][spec-4.4]") {
    // §4.4: "Parameters: N (Number of entities), DE1 ... DEN
    //   (Pointers to DE of each constituent entity)"
    ParamTokenizer tok("3,1,3,5;", ',', ';');
    auto r = parse_composite_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().constituents.size() == 3);
    CHECK(r.value().constituents[0].value == 1);
    CHECK(r.value().constituents[1].value == 3);
    CHECK(r.value().constituents[2].value == 5);
}

TEST_CASE("§4.4 — parse composite curve with 1 constituent", "[entity][spec-4.4]") {
    // §4.4: "N = Number of entities"
    ParamTokenizer tok("1,7;", ',', ';');
    auto r = parse_composite_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().constituents.size() == 1);
    CHECK(r.value().constituents[0].value == 7);
}

// ─────────────────────────────────────────────────────────────────
// §4.4: "N = Number of entities"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.4 — N=0 gives empty constituent list", "[entity][spec-4.4]") {
    // §4.4: "N = Number of entities" — when N=0, no constituents
    ParamTokenizer tok("0;", ',', ';');
    auto r = parse_composite_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().constituents.empty());
}

// ─────────────────────────────────────────────────────────────────
// §4.4: Multiple constituents
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.4 — composite curve with many constituents", "[entity][spec-4.4]") {
    // §4.4: "an ordered list of entities"
    std::string data = "5,10,20,30,40,50;";
    ParamTokenizer tok(data, ',', ';');
    auto r = parse_composite_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().constituents.size() == 5);
    CHECK(r.value().constituents[4].value == 50);
}
