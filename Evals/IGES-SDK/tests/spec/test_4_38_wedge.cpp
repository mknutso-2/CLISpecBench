// Tests for §4.38 — Right Angular Wedge Entity (Type 152).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/wedge_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.38 — parse wedge with all parameters", "[entity][spec-4.38]") {
    // §4.38: "Parameters: LX, LY, LZ, LTX, X1, Y1, Z1, I1, J1, K1, I2, J2, K2"
    ParamTokenizer tok("10.0,5.0,3.0,4.0,1.0,2.0,3.0,1.0,0.0,0.0,0.0,0.0,1.0;", ',', ';');
    auto r = parse_wedge_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().lx == 10.0);
    CHECK(r.value().ly == 5.0);
    CHECK(r.value().lz == 3.0);
    CHECK(r.value().ltx == 4.0);
    CHECK(r.value().corner.x == 1.0);
}

TEST_CASE("§4.38 — wedge with LTX=0 five faces", "[entity][spec-4.38]") {
    // §4.38: "If LTX=0, the wedge has five faces, two of which are triangular"
    ParamTokenizer tok("10.0,5.0,3.0,0.0,,,,,,,,,,;", ',', ';');
    auto r = parse_wedge_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().ltx == 0.0);
}
