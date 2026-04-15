// Tests for §4.147 — Shell Entity (Type 514).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/shell_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.147 — parse shell with 1 face", "[entity][spec-4.147]") {
    // §4.147: "N: Number of faces"
    //         "FACE(i): Pointer to face DE"
    //         "OF(i): Orientation flag"
    ParamTokenizer tok("1,3,1;", ',', ';');
    auto r = parse_shell_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 1);
    REQUIRE(r.value().faces.size() == 1);
    CHECK(r.value().faces[0].face.value == 3);
    CHECK(r.value().faces[0].orientation == true);
}

TEST_CASE("§4.147 — parse shell with multiple faces", "[entity][spec-4.147]") {
    ParamTokenizer tok("2,3,1,5,0;", ',', ';');
    auto r = parse_shell_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 2);
    CHECK(r.value().faces[1].face.value == 5);
    CHECK(r.value().faces[1].orientation == false);
}
