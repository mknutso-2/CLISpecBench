// Tests for §4.93 — Color Definition Entity (Type 314).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/color_definition_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.93: "Parameters: CC1, CC2, CC3, CNAME"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.93 — parse color definition with name", "[entity][spec-4.93]") {
    // §4.93: "CC1: Red component of color (0.0-100.0 percent)"
    //        "CC2: Green component of color (0.0-100.0 percent)"
    //        "CC3: Blue component of color (0.0-100.0 percent)"
    //        "CNAME: Color name"
    ParamTokenizer tok("100.0,0.0,0.0,3HRed;", ',', ';');
    auto r = parse_color_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().red == 100.0);
    CHECK(r.value().green == 0.0);
    CHECK(r.value().blue == 0.0);
    CHECK(r.value().name == "Red");
}

TEST_CASE("§4.93 — parse color definition without name", "[entity][spec-4.93]") {
    // §4.93: "CNAME: Color name" — optional, may be defaulted
    ParamTokenizer tok("50.0,50.0,50.0;", ',', ';');
    auto r = parse_color_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().red == 50.0);
    CHECK(r.value().green == 50.0);
    CHECK(r.value().blue == 50.0);
    CHECK(r.value().name.empty());
}

TEST_CASE("§4.93 — color components are percentages", "[entity][spec-4.93]") {
    // §4.93: "CC1, CC2, CC3 ... are real numbers in the range 0.0 to 100.0"
    ParamTokenizer tok("0.0,100.0,50.5;", ',', ';');
    auto r = parse_color_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().red == 0.0);
    CHECK(r.value().green == 100.0);
    CHECK(r.value().blue == 50.5);
}
