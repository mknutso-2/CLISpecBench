// Tests for §4.28 — Finite Element Entity (Type 136).
// Spec reference: IGES 5.3, §4.28, pages 137-152.

#include <catch2/catch_test_macros.hpp>
#include "entities/finite_element_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.28: "Parameters: ITOP, N, DE(1)..DE(N), ETYP"
// -----------------------------------------------------------------

TEST_CASE("§4.28 — parse BEAM element (ITOP=1, N=2)", "[entity][spec-4.28]") {
    // §4.28 Table 6: BEAM = topology type 1, 2 nodes
    ParamTokenizer tok("1,2,3,5,4HBEAM;", ',', ';');
    auto r = parse_finite_element_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->itop == 1);
    CHECK(r->n == 2);
    CHECK(r->nodes.size() == 2);
    CHECK(r->nodes[0].value == 3);
    CHECK(r->nodes[1].value == 5);
    CHECK(r->etyp == "BEAM");
}

// -----------------------------------------------------------------
// §4.28 Table 6: LTRIA = topology type 2, 3 nodes
// -----------------------------------------------------------------

TEST_CASE("§4.28 — parse LTRIA element (ITOP=2, N=3)", "[entity][spec-4.28]") {
    // §4.28 Table 6: Linear Triangle = topology type 2, 3 nodes
    ParamTokenizer tok("2,3,1,3,5,5HLTRIA;", ',', ';');
    auto r = parse_finite_element_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->itop == 2);
    CHECK(r->n == 3);
    CHECK(r->nodes.size() == 3);
    CHECK(r->etyp == "LTRIA");
}

// -----------------------------------------------------------------
// §4.28 Table 6: LSO = topology type 17, 8 nodes (Linear Solid)
// -----------------------------------------------------------------

TEST_CASE("§4.28 — parse LSO element (ITOP=17, N=8)", "[entity][spec-4.28]") {
    // §4.28 Table 6: Linear Solid = topology type 17, 8 nodes
    ParamTokenizer tok("17,8,1,3,5,7,9,11,13,15,3HLSO;", ',', ';');
    auto r = parse_finite_element_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->itop == 17);
    CHECK(r->n == 8);
    CHECK(r->nodes.size() == 8);
    CHECK(r->nodes[0].value == 1);
    CHECK(r->nodes[7].value == 15);
    CHECK(r->etyp == "LSO");
}

// -----------------------------------------------------------------
// §4.28: "A missing node ... shall have its corresponding pointer
//   value set equal to zero."
// -----------------------------------------------------------------

TEST_CASE("§4.28 — zero pointer for missing node", "[entity][spec-4.28]") {
    // §4.28: Missing nodes have pointer = 0
    ParamTokenizer tok("1,2,3,0,4HBEAM;", ',', ';');
    auto r = parse_finite_element_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->nodes[0].value == 3);
    CHECK(r->nodes[1].value == 0);
}

// -----------------------------------------------------------------
// Round-trip: write then parse
// -----------------------------------------------------------------

TEST_CASE("§4.28 — round-trip finite element entity", "[entity][spec-4.28]") {
    FiniteElementEntity orig;
    orig.itop = 5;
    orig.n = 4;
    orig.nodes = {DEIndex{10}, DEIndex{12}, DEIndex{14}, DEIndex{16}};
    orig.etyp = "LQUAD";

    auto pd = write_finite_element_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_finite_element_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->itop == orig.itop);
    CHECK(r->n == orig.n);
    CHECK(r->nodes.size() == 4);
    CHECK(r->nodes[0].value == 10);
    CHECK(r->nodes[1].value == 12);
    CHECK(r->nodes[2].value == 14);
    CHECK(r->nodes[3].value == 16);
    CHECK(r->etyp == orig.etyp);
}
