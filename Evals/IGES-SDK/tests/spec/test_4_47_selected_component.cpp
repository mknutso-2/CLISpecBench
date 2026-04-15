// Tests for §4.47 — Selected Component Entity (Type 182).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/selected_component_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

TEST_CASE("§4.47 — parse selected component", "[entity][spec-4.47]") {
    // §4.47: "Parameters: BTREE, SELX, SELY, SELZ"
    //        "BTREE: Pointer to the DE of the Boolean Tree Entity"
    //        "SELX, SELY, SELZ: components of a point in or on
    //         the desired component"
    ParamTokenizer tok("5,1.0,2.0,3.0;", ',', ';');
    auto r = parse_selected_component_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().btree.value == 5);
    CHECK(r.value().sel_point.x == 1.0);
    CHECK(r.value().sel_point.y == 2.0);
    CHECK(r.value().sel_point.z == 3.0);
}
