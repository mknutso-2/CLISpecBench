// Tests for §4.143.1 — Vertex List Entity (Type 502, Form 1).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/vertex_list_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.143.1 — parse vertex list with 2 vertices", "[entity][spec-4.143]") {
    // §4.143.1: "N: Number of vertex tuples in list (N > 0)"
    //           "X(i), Y(i), Z(i): coordinates of vertex i"
    ParamTokenizer tok("2,1.0,2.0,3.0,4.0,5.0,6.0;", ',', ';');
    auto r = parse_vertex_list_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 2);
    REQUIRE(r.value().vertices.size() == 2);
    CHECK(r.value().vertices[0].x == 1.0);
    CHECK(r.value().vertices[0].y == 2.0);
    CHECK(r.value().vertices[0].z == 3.0);
    CHECK(r.value().vertices[1].x == 4.0);
    CHECK(r.value().vertices[1].y == 5.0);
    CHECK(r.value().vertices[1].z == 6.0);
}

TEST_CASE("§4.143.1 — parse vertex list single vertex", "[entity][spec-4.143]") {
    ParamTokenizer tok("1,0.0,0.0,0.0;", ',', ';');
    auto r = parse_vertex_list_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 1);
    REQUIRE(r.value().vertices.size() == 1);
}
