// Tests for §4.142 — Solid Instance Entity (Type 430).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/solid_instance_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.142 — parse solid instance", "[entity][spec-4.142]") {
    // §4.142: "PTR: Pointer to the DE of the solid"
    ParamTokenizer tok("7;", ',', ';');
    auto r = parse_solid_instance_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().ptr.value == 7);
}
