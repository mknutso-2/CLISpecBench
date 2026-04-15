// Tests for §4.57 — General Label Entity (Type 210).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/general_label_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.57: "Parameters: DENOTE, N, DEARRW(1)..DEARRW(N)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.57 — parse general label with 2 leaders", "[entity][spec-4.57]") {
    // §4.57: "DENOTE: Pointer to the General Note Entity"
    //        "N: Number of associated leader entities"
    //        "DEARRW(i): Pointers to leader entities"
    ParamTokenizer tok("1,2,3,5;", ',', ';');
    auto r = parse_general_label_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().denote.value == 1);
    CHECK(r.value().n == 2);
    REQUIRE(r.value().leaders.size() == 2);
    CHECK(r.value().leaders[0].value == 3);
    CHECK(r.value().leaders[1].value == 5);
}

TEST_CASE("§4.57 — general label with no leaders", "[entity][spec-4.57]") {
    // §4.57: "N: Number of associated leader entities"
    ParamTokenizer tok("1,0;", ',', ';');
    auto r = parse_general_label_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().n == 0);
    CHECK(r.value().leaders.empty());
}
