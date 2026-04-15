// Tests for §4.97 — Property Entity (Type 406).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/property_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.97: "Parameters: NP, then NP values"
//   The Property Entity is a general-purpose form-dependent entity.
//   The form number determines the interpretation of the data.
//   We store the raw values as a generic list.
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.97 — parse property entity Form 1 (definition levels)", "[entity][spec-4.97]") {
    // §4.97 Form 1: "NP: Number of property values"
    //               "V(i): Property values (integers = level numbers)"
    ParamTokenizer tok("2,5,10;", ',', ';');
    auto r = parse_property_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().np == 2);
    REQUIRE(r.value().values.size() == 2);
}

TEST_CASE("§4.97 — parse property entity with 0 values", "[entity][spec-4.97]") {
    // §4.97: "NP: Number of property values"
    ParamTokenizer tok("0;", ',', ';');
    auto r = parse_property_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().np == 0);
    CHECK(r.value().values.empty());
}

TEST_CASE("§4.97 — parse property entity with string values", "[entity][spec-4.97]") {
    // §4.97: Property values can be integer, real, or string
    //   depending on the form number. We store the raw FieldValues.
    ParamTokenizer tok("1,5HLabel;", ',', ';');
    auto r = parse_property_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().np == 1);
    REQUIRE(r.value().values.size() == 1);
}
