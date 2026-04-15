// Tests for §4.40 — Right Circular Cone Frustum Entity (Type 156).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/cone_frustum_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.40 — parse cone frustum", "[entity][spec-4.40]") {
    // §4.40: "Parameters: H, R1, R2, X1, Y1, Z1, I1, J1, K1"
    ParamTokenizer tok("10.0,5.0,2.0,0.0,0.0,0.0,0.0,0.0,1.0;", ',', ';');
    auto r = parse_cone_frustum_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().h == 10.0);
    CHECK(r.value().r1 == 5.0);
    CHECK(r.value().r2 == 2.0);
}

TEST_CASE("§4.40 — cone apex R2=0", "[entity][spec-4.40]") {
    // §4.40: "R2: Smaller face radius (zero for cone apex — default)"
    ParamTokenizer tok("10.0,5.0,,,,,,,;", ',', ';');
    auto r = parse_cone_frustum_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().r2 == 0.0);
}
