// Tests for §4.58 — General Note Entity (Type 212).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/general_note_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.58: "Parameters: NS, then per-string: NC(i), WC(i), HC(i),
//   FC(i), SL(i), A(i), M(i), VH(i), XS(i), YS(i), ZS(i),
//   STRING(i)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.58 — parse general note with 1 string", "[entity][spec-4.58]") {
    // §4.58: "NS: Number of text strings in this entity"
    //        "NC(i): Number of characters in string i (or Hollerith count)"
    //        "WC(i): Character width"
    //        "HC(i): Character height"
    //        "FC(i): Font code"
    //        "SL(i): Slant angle in radians"
    //        "A(i): Rotation angle in radians"
    //        "M(i): Mirror flag (0=none, 1=mirror about Y, 2=mirror about X)"
    //        "VH(i): Rotate internal text flag (0=horizontal, 1=vertical)"
    //        "XS(i), YS(i), ZS(i): Start point of text string"
    //        "STRING(i): The text string"
    ParamTokenizer tok("1,5,1.0,2.0,1,0.0,0.0,0,0,10.0,20.0,0.0,5HHello;", ',', ';');
    auto r = parse_general_note_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().ns == 1);
    REQUIRE(r.value().strings.size() == 1);
    CHECK(r.value().strings[0].nc == 5);
    CHECK(r.value().strings[0].wc == 1.0);
    CHECK(r.value().strings[0].hc == 2.0);
    CHECK(r.value().strings[0].fc == 1);
    CHECK(r.value().strings[0].slant == 0.0);
    CHECK(r.value().strings[0].angle == 0.0);
    CHECK(r.value().strings[0].mirror == 0);
    CHECK(r.value().strings[0].vh == 0);
    CHECK(r.value().strings[0].start.x == 10.0);
    CHECK(r.value().strings[0].start.y == 20.0);
    CHECK(r.value().strings[0].start.z == 0.0);
    CHECK(r.value().strings[0].text == "Hello");
}

TEST_CASE("§4.58 — parse general note with 2 strings", "[entity][spec-4.58]") {
    // §4.58: "NS: Number of text strings"
    ParamTokenizer tok(
        "2,"
        "2,1.0,1.0,1,0.0,0.0,0,0,0.0,0.0,0.0,2HHi,"
        "3,1.0,1.0,1,0.0,0.0,0,0,5.0,0.0,0.0,3HBye;",
        ',', ';');
    auto r = parse_general_note_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().ns == 2);
    REQUIRE(r.value().strings.size() == 2);
    CHECK(r.value().strings[0].text == "Hi");
    CHECK(r.value().strings[1].text == "Bye");
    CHECK(r.value().strings[1].start.x == 5.0);
}
