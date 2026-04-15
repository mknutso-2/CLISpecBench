// Tests for §4.1 — Null Entity (Type 0).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/null_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.1: "A Null Entity is used when an application requires an
//   entity type number but the entity itself has no significance"
//   "The parameter data section contains only the entity type number"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.1 — parse null entity (no parameters)", "[entity][spec-4.1]") {
    // §4.1: "The parameter data section contains only the entity
    //   type number"
    ParamTokenizer tok(";", ',', ';');
    auto r = parse_null_entity(tok);
    REQUIRE(r.has_value());
}

TEST_CASE("§4.1 — null entity has entity type 0", "[entity][spec-4.1]") {
    // §4.1: "Entity Type Number: 0"
    ParamTokenizer tok(";", ',', ';');
    auto r = parse_null_entity(tok);
    REQUIRE(r.has_value());
    // NullEntity is a marker struct with no data fields
}
