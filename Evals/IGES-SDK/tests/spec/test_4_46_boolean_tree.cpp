// Tests for §4.46 — Boolean Tree Entity (Type 180).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/boolean_tree_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.46 — parse boolean tree simple union", "[entity][spec-4.46]") {
    // §4.46: "N: Length of post-order notation"
    //        "A positive value implies an operation code;
    //         a negative value implies the absolute value is a pointer"
    //        "1 = Union, 2 = Intersection, 3 = Difference"
    // Post-order: operand A, operand B, union
    ParamTokenizer tok("3,-1,-3,1;", ',', ';');
    auto r = parse_boolean_tree_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 3);
    REQUIRE(r.value().entries.size() == 3);
    // Operands are negative (pointers)
    CHECK(r.value().entries[0] == -1);
    CHECK(r.value().entries[1] == -3);
    // Operation is positive
    CHECK(r.value().entries[2] == 1);
}

TEST_CASE("§4.46 — parse boolean tree spec example", "[entity][spec-4.46]") {
    // §4.46 Figure 57 example: 5 operands + 4 operations = N=9
    // Post-order: 9, PTRA, PTRB, PTRC, 1, 3, PTRD, PTRE, 2, 1
    // N=9 then 9 entries
    ParamTokenizer tok("9,-1,-3,-5,1,3,-7,-9,2,1;", ',', ';');
    auto r = parse_boolean_tree_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 9);
    REQUIRE(r.value().entries.size() == 9);
}

TEST_CASE("§4.46 — boolean tree difference", "[entity][spec-4.46]") {
    // §4.46: "3 = Difference"
    ParamTokenizer tok("3,-5,-7,3;", ',', ';');
    auto r = parse_boolean_tree_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().entries[2] == 3);
}
