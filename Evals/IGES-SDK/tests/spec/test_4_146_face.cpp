// Tests for §4.146 — Face Entity (Type 510, Form 1).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/face_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.146 — parse face with 1 loop", "[entity][spec-4.146]") {
    // §4.146: "SURF: Pointer to underlying surface"
    //         "N: Number of loops"
    //         "OF: Outer loop flag"
    //         "LOOP(1)..LOOP(N): Loop pointers"
    ParamTokenizer tok("3,1,1,5;", ',', ';');
    auto r = parse_face_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().surf.value == 3);
    CHECK(r.value().n == 1);
    CHECK(r.value().outer_loop_flag == true);
    REQUIRE(r.value().loops.size() == 1);
    CHECK(r.value().loops[0].value == 5);
}

TEST_CASE("§4.146 — parse face with multiple loops", "[entity][spec-4.146]") {
    // §4.146: "If more than one loop bounds a face, the loops shall be disjoint"
    ParamTokenizer tok("3,3,1,5,7,9;", ',', ';');
    auto r = parse_face_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 3);
    REQUIRE(r.value().loops.size() == 3);
    CHECK(r.value().loops[2].value == 9);
}
