// Tests for §4.145 — Loop Entity (Type 508, Form 1).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/loop_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.145 — parse loop with 1 edge use, no param curves", "[entity][spec-4.145]") {
    // §4.145: "N: Number of edge tuples"
    //         "TYPE(i): 0=Edge, 1=Vertex"
    //         "EDGE(i): Pointer to Edge/Vertex List"
    //         "NDX(i): List index"
    //         "OF(i): Orientation flag"
    //         "K(i): Number of parameter space curves"
    ParamTokenizer tok("1,0,3,1,1,0;", ',', ';');
    auto r = parse_loop_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 1);
    REQUIRE(r.value().edge_uses.size() == 1);
    CHECK(r.value().edge_uses[0].type == 0);
    CHECK(r.value().edge_uses[0].edge.value == 3);
    CHECK(r.value().edge_uses[0].ndx == 1);
    CHECK(r.value().edge_uses[0].orientation == true);
    CHECK(r.value().edge_uses[0].k == 0);
}

TEST_CASE("§4.145 — parse loop with param space curves", "[entity][spec-4.145]") {
    // §4.145: "ISOP(i,j): Isoparametric flag"
    //         "CURV(i,j): Pointer to parameter space curve"
    ParamTokenizer tok("1,0,3,1,1,1,0,5;", ',', ';');
    auto r = parse_loop_entity(tok);
    REQUIRE(r.has_value());
    REQUIRE(r.value().edge_uses.size() == 1);
    CHECK(r.value().edge_uses[0].k == 1);
    REQUIRE(r.value().edge_uses[0].param_curves.size() == 1);
    CHECK(r.value().edge_uses[0].param_curves[0].isoparametric == false);
    CHECK(r.value().edge_uses[0].param_curves[0].curve.value == 5);
}
