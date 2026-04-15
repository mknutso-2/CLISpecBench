// Tests for §4.48 — Solid Assembly Entity (Type 184).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/solid_assembly_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.48 — parse solid assembly with 2 items", "[entity][spec-4.48]") {
    // §4.48: "N: Number of items"
    //        "PTR(1)..PTR(N): Pointers to item DEs"
    //        "PTRM(1)..PTRM(N): Pointers to Transformation Matrix DEs"
    ParamTokenizer tok("2,3,5,7,9;", ',', ';');
    auto r = parse_solid_assembly_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 2);
    REQUIRE(r.value().items.size() == 2);
    CHECK(r.value().items[0].value == 3);
    CHECK(r.value().items[1].value == 5);
    REQUIRE(r.value().transforms.size() == 2);
    CHECK(r.value().transforms[0].value == 7);
    CHECK(r.value().transforms[1].value == 9);
}

TEST_CASE("§4.48 — assembly with zero transform pointers", "[entity][spec-4.48]") {
    // §4.48: "A value of zero in the pointer field indicates
    //   the identity matrix"
    ParamTokenizer tok("1,3,0;", ',', ';');
    auto r = parse_solid_assembly_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().transforms[0].value == 0);
}
