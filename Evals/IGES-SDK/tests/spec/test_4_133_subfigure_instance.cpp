// Tests for §4.133 — Singular Subfigure Instance Entity (Type 408).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/subfigure_instance_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.133: "Parameters: DE, X, Y, Z, S"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.133 — parse singular subfigure instance", "[entity][spec-4.133]") {
    // §4.133: "DE: Pointer to the DE of the Subfigure Definition Entity"
    //         "X, Y, Z: Translation data relative to the Subfigure
    //          Definition origin"
    //         "S: Scale factor (default 1.0)"
    ParamTokenizer tok("5,10.0,20.0,30.0,2.0;", ',', ';');
    auto r = parse_subfigure_instance_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().de.value == 5);
    CHECK(r.value().translation.x == 10.0);
    CHECK(r.value().translation.y == 20.0);
    CHECK(r.value().translation.z == 30.0);
    CHECK(r.value().scale == 2.0);
}

TEST_CASE("§4.133 — scale defaults to 1.0", "[entity][spec-4.133]") {
    // §4.133: "S: Scale factor (default 1.0)"
    ParamTokenizer tok("3,0.0,0.0,0.0;", ',', ';');
    auto r = parse_subfigure_instance_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().scale == 1.0);
}
