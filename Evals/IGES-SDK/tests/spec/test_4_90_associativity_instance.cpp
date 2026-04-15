// Tests for §4.90 — Associativity Instance Entity (Type 402).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/associativity_instance_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.90: "The Associativity Instance Entity defines an occurrence
//   of a given Associativity."
//   The most commonly used form is Form 1 (Group Associativity).
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.90 — Form 1: group with back-pointers", "[entity][spec-4.90]") {
    // §4.90 Form 1: "N: Number of entries"
    //               "DE(1)..DE(N): Pointers to grouped entities"
    ParamTokenizer tok("3,1,3,5;", ',', ';');
    auto r = parse_associativity_instance_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 3);
    REQUIRE(r.value().entries.size() == 3);
    CHECK(r.value().entries[0].value == 1);
    CHECK(r.value().entries[1].value == 3);
    CHECK(r.value().entries[2].value == 5);
}

TEST_CASE("§4.90 — empty group (N=0)", "[entity][spec-4.90]") {
    // §4.90: "N: Number of entries"
    ParamTokenizer tok("0;", ',', ';');
    auto r = parse_associativity_instance_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 0);
    CHECK(r.value().entries.empty());
}
