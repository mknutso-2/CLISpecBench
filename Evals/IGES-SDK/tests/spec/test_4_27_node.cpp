// Tests for §4.27 — Node Entity (Type 134).
// Spec reference: IGES 5.3, §4.27, pages 134-136.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/node_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// -----------------------------------------------------------------
// §4.27: "Parameters: X/R/R, Y/θ/θ, Z/Z/φ, NDCSP"
// -----------------------------------------------------------------

TEST_CASE("§4.27 — parse node entity", "[entity][spec-4.27]") {
    // §4.27 PD: "Index 1: X/R/R, 2: Y/θ/θ, 3: Z/Z/φ, 4: NDCSP"
    ParamTokenizer tok("10.0,20.0,30.0,5;", ',', ';');
    auto r = parse_node_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->x, WithinRel(10.0));
    CHECK_THAT(r->y, WithinRel(20.0));
    CHECK_THAT(r->z, WithinRel(30.0));
    CHECK(r->ndcsp.value == 5);
}

// -----------------------------------------------------------------
// §4.27: "Default (zero) is Global Cartesian Coordinate System"
// -----------------------------------------------------------------

TEST_CASE("§4.27 — NDCSP defaults to zero (Global Cartesian)", "[entity][spec-4.27]") {
    // §4.27: NDCSP default is zero
    ParamTokenizer tok("1.0,2.0,3.0;", ',', ';');
    auto r = parse_node_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ndcsp.value == 0);
}

// -----------------------------------------------------------------
// §4.27: Node at origin
// -----------------------------------------------------------------

TEST_CASE("§4.27 — node at origin", "[entity][spec-4.27]") {
    ParamTokenizer tok("0.0,0.0,0.0,0;", ',', ';');
    auto r = parse_node_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->x, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r->y, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r->z, WithinAbs(0.0, 1e-15));
}

// -----------------------------------------------------------------
// Round-trip: write then parse
// -----------------------------------------------------------------

TEST_CASE("§4.27 — round-trip node entity", "[entity][spec-4.27]") {
    NodeEntity orig;
    orig.x = 100.5; orig.y = -200.3; orig.z = 50.7;
    orig.ndcsp = DEIndex{9};

    auto pd = write_node_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_node_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->x, WithinRel(orig.x));
    CHECK_THAT(r->y, WithinRel(orig.y));
    CHECK_THAT(r->z, WithinRel(orig.z));
    CHECK(r->ndcsp.value == orig.ndcsp.value);
}
