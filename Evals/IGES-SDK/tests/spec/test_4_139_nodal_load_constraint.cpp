// Tests for §4.139 — Nodal Load/Constraint Entity (Type 418).
// Spec reference: IGES 5.3, §4.139, page 506.

#include <catch2/catch_test_macros.hpp>
#include "entities/nodal_load_constraint_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.139: "Parameters: NC, TYPE, DE, PTR(1..NC)"
// -----------------------------------------------------------------

TEST_CASE("§4.139 — parse nodal load (1 case)", "[entity][spec-4.139]") {
    // §4.139 PD: NC=1, TYPE=1 (loads), DE=5, PTR(1)=7
    ParamTokenizer tok("1,1,5,7;", ',', ';');
    auto r = parse_nodal_load_constraint_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->nc == 1);
    CHECK(r->type == 1);
    CHECK(r->de.value == 5);
    REQUIRE(r->ptrs.size() == 1);
    CHECK(r->ptrs[0].value == 7);
}

// -----------------------------------------------------------------
// §4.139: TYPE=2 means constraints
// -----------------------------------------------------------------

TEST_CASE("§4.139 — parse constraint with multiple cases", "[entity][spec-4.139]") {
    // §4.139 PD: NC=3, TYPE=2 (constraints), DE=11, PTR(1..3)=13,15,17
    ParamTokenizer tok("3,2,11,13,15,17;", ',', ';');
    auto r = parse_nodal_load_constraint_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->nc == 3);
    CHECK(r->type == 2);
    CHECK(r->de.value == 11);
    REQUIRE(r->ptrs.size() == 3);
    CHECK(r->ptrs[0].value == 13);
    CHECK(r->ptrs[1].value == 15);
    CHECK(r->ptrs[2].value == 17);
}

// -----------------------------------------------------------------
// Round-trip: write then parse
// -----------------------------------------------------------------

TEST_CASE("§4.139 — round-trip nodal load/constraint", "[entity][spec-4.139]") {
    NodalLoadConstraintEntity orig;
    orig.nc = 2;
    orig.type = 1;
    orig.de = DEIndex{9};
    orig.ptrs = {DEIndex{11}, DEIndex{13}};

    auto pd = write_nodal_load_constraint_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_nodal_load_constraint_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->nc == orig.nc);
    CHECK(r->type == orig.type);
    CHECK(r->de.value == 9);
    REQUIRE(r->ptrs.size() == 2);
    CHECK(r->ptrs[0].value == 11);
    CHECK(r->ptrs[1].value == 13);
}
