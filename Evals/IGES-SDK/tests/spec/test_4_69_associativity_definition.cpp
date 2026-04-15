// Tests for §4.69 — Associativity Definition Entity (Type 302).
// Spec reference: IGES 5.3, §4.69, page 290.

#include <catch2/catch_test_macros.hpp>
#include "entities/associativity_definition_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.69: "Parameters: K, {BP(i), OR(i), N(i), IT(i,1..N(i))} x K"
// -----------------------------------------------------------------

TEST_CASE("§4.69 — parse single-class associativity definition", "[entity][spec-4.69]") {
    // K=1, BP=1 (back ptrs required), OR=1 (ordered), N=2, IT(1)=1 (pointer), IT(2)=2 (value)
    ParamTokenizer tok("1,1,1,2,1,2;", ',', ';');
    auto r = parse_associativity_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->k == 1);
    REQUIRE(r->classes.size() == 1);
    CHECK(r->classes[0].bp == 1);
    CHECK(r->classes[0].order == 1);
    CHECK(r->classes[0].n == 2);
    REQUIRE(r->classes[0].item_types.size() == 2);
    CHECK(r->classes[0].item_types[0] == 1);
    CHECK(r->classes[0].item_types[1] == 2);
}

// -----------------------------------------------------------------
// §4.69: Multiple classes
// -----------------------------------------------------------------

TEST_CASE("§4.69 — parse multi-class definition", "[entity][spec-4.69]") {
    // K=2, class1: BP=2 (no back ptrs), OR=2 (unordered), N=1, IT=1 (pointer)
    //       class2: BP=1, OR=1, N=3, IT=3,3,3 (value-or-pointer)
    ParamTokenizer tok("2,2,2,1,1,1,1,3,3,3,3;", ',', ';');
    auto r = parse_associativity_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->k == 2);
    REQUIRE(r->classes.size() == 2);

    CHECK(r->classes[0].bp == 2);
    CHECK(r->classes[0].order == 2);
    CHECK(r->classes[0].n == 1);
    CHECK(r->classes[0].item_types[0] == 1);

    CHECK(r->classes[1].bp == 1);
    CHECK(r->classes[1].order == 1);
    CHECK(r->classes[1].n == 3);
    REQUIRE(r->classes[1].item_types.size() == 3);
    CHECK(r->classes[1].item_types[0] == 3);
    CHECK(r->classes[1].item_types[1] == 3);
    CHECK(r->classes[1].item_types[2] == 3);
}

// -----------------------------------------------------------------
// Round-trip: write then parse
// -----------------------------------------------------------------

TEST_CASE("§4.69 — round-trip associativity definition", "[entity][spec-4.69]") {
    AssociativityDefinitionEntity orig;
    orig.k = 2;

    AssociativityClass c1;
    c1.bp = 1; c1.order = 1; c1.n = 2;
    c1.item_types = {1, 2};
    orig.classes.push_back(c1);

    AssociativityClass c2;
    c2.bp = 2; c2.order = 2; c2.n = 1;
    c2.item_types = {3};
    orig.classes.push_back(c2);

    auto pd = write_associativity_definition_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_associativity_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->k == 2);
    REQUIRE(r->classes.size() == 2);
    CHECK(r->classes[0].bp == 1);
    CHECK(r->classes[0].order == 1);
    CHECK(r->classes[0].item_types == std::vector{1, 2});
    CHECK(r->classes[1].bp == 2);
    CHECK(r->classes[1].item_types == std::vector{3});
}
