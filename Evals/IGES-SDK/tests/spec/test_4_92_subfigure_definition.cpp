// Tests for §4.92 — Subfigure Definition Entity (Type 308).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/subfigure_definition_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.92: "Parameters: DEPTH, NAME, N, DE(1)..DE(N)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.92 — parse subfigure definition with 2 entities", "[entity][spec-4.92]") {
    // §4.92: "DEPTH: Depth of subfigure nesting (integer ≥ 0)"
    //        "NAME: Subfigure name"
    //        "N: Number of associated entities"
    //        "DE(i): Pointers to associated entities"
    ParamTokenizer tok("1,5HBlock,2,3,5;", ',', ';');
    auto r = parse_subfigure_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().depth == 1);
    CHECK(r.value().name == "Block");
    CHECK(r.value().n == 2);
    REQUIRE(r.value().entities.size() == 2);
    CHECK(r.value().entities[0].value == 3);
    CHECK(r.value().entities[1].value == 5);
}

TEST_CASE("§4.92 — depth 0 means no nesting", "[entity][spec-4.92]") {
    // §4.92: "DEPTH: Depth of subfigure nesting"
    //        Depth 0 = a leaf subfigure with no nested subfigure instances
    ParamTokenizer tok("0,4HLeaf,1,7;", ',', ';');
    auto r = parse_subfigure_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().depth == 0);
    CHECK(r.value().name == "Leaf");
}

TEST_CASE("§4.92 — empty subfigure definition (N=0)", "[entity][spec-4.92]") {
    // §4.92: "N: Number of associated entities"
    ParamTokenizer tok("0,5HEmpty,0;", ',', ';');
    auto r = parse_subfigure_definition_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 0);
    CHECK(r.value().entities.empty());
}
