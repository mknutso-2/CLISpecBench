// Tests for §4.144.1 — Edge List Entity (Type 504, Form 1).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/edge_list_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.144.1 — parse edge list with 1 edge", "[entity][spec-4.144]") {
    // §4.144.1: "N: Number of edge tuples"
    //           "CURV(i): Pointer to model space curve"
    //           "SVP(i), SV(i): start vertex pointer and index"
    //           "TVP(i), TV(i): terminate vertex pointer and index"
    ParamTokenizer tok("1,5,1,1,1,2;", ',', ';');
    auto r = parse_edge_list_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 1);
    REQUIRE(r.value().edges.size() == 1);
    CHECK(r.value().edges[0].curve.value == 5);
    CHECK(r.value().edges[0].svp.value == 1);
    CHECK(r.value().edges[0].sv == 1);
    CHECK(r.value().edges[0].tvp.value == 1);
    CHECK(r.value().edges[0].tv == 2);
}

TEST_CASE("§4.144.1 — parse edge list with 2 edges", "[entity][spec-4.144]") {
    ParamTokenizer tok("2,5,1,1,1,2,7,1,2,1,3;", ',', ';');
    auto r = parse_edge_list_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 2);
    REQUIRE(r.value().edges.size() == 2);
    CHECK(r.value().edges[1].curve.value == 7);
}
