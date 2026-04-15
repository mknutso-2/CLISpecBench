// Tests for §4.26 — Connect Point Entity (Type 132).
// Spec reference: IGES 5.3, §4.26, pages 131-133.

#include <catch2/catch_test_macros.hpp>
#include "entities/connect_point_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.26 PD table (page 133): X, Y, Z, PTR, TF, FF, CID, PTTCID,
//   CFN, PTTCFN, CPID, FC, SF, PSFI — 14 parameters total.
// -----------------------------------------------------------------

TEST_CASE("§4.26 — parse connect point with all 14 fields", "[entity][spec-4.26]") {
    // All 14 PD fields per spec page 133
    ParamTokenizer tok("1.0,2.0,3.0,0,0,1,"
                       "4Hpwr1,0,5Hpower,0,"
                       "42,10,0,0;", ',', ';');
    auto r = parse_connect_point_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->location.x == 1.0);
    CHECK(r->location.y == 2.0);
    CHECK(r->location.z == 3.0);
    CHECK(r->display_symbol.is_null());
    CHECK(r->tf == 0);
    CHECK(r->ff == 1);
    CHECK(r->cid == "pwr1");
    CHECK(r->pttcid.is_null());
    CHECK(r->cfn == "power");
    CHECK(r->pttcfn.is_null());
    CHECK(r->cpid == 42);
    CHECK(r->fc == 10);
    CHECK(r->sf == 0);
    CHECK(r->psfi.is_null());
}

TEST_CASE("§4.26 — parse connect point with display symbol and text templates", "[entity][spec-4.26]") {
    // §4.26: PTR points to display symbol geometry; PTTCID/PTTCFN point to text templates
    ParamTokenizer tok("0.0,0.0,0.0,5,101,2,"
                       "3Habc,7,4Htest,9,"
                       "100,25,1,11;", ',', ';');
    auto r = parse_connect_point_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->display_symbol.value == 5);
    CHECK(r->tf == 101);
    CHECK(r->ff == 2);
    CHECK(r->cid == "abc");
    CHECK(r->pttcid.value == 7);
    CHECK(r->cfn == "test");
    CHECK(r->pttcfn.value == 9);
    CHECK(r->cpid == 100);
    CHECK(r->fc == 25);
    CHECK(r->sf == 1);
    CHECK(r->psfi.value == 11);
}

TEST_CASE("§4.26 — round-trip connect point", "[entity][spec-4.26]") {
    ConnectPointEntity orig;
    orig.location = {10.0, 20.0, 30.0};
    orig.display_symbol = DEIndex{3};
    orig.tf = 101;
    orig.ff = 1;
    orig.cid = "PIN1";
    orig.pttcid = DEIndex{5};
    orig.cfn = "INPUT";
    orig.pttcfn = DEIndex{7};
    orig.cpid = 42;
    orig.fc = 12;
    orig.sf = 1;
    orig.psfi = DEIndex{9};

    auto pd = write_connect_point_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_connect_point_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->location.x == 10.0);
    CHECK(r->location.y == 20.0);
    CHECK(r->location.z == 30.0);
    CHECK(r->display_symbol.value == 3);
    CHECK(r->tf == 101);
    CHECK(r->ff == 1);
    CHECK(r->cid == "PIN1");
    CHECK(r->pttcid.value == 5);
    CHECK(r->cfn == "INPUT");
    CHECK(r->pttcfn.value == 7);
    CHECK(r->cpid == 42);
    CHECK(r->fc == 12);
    CHECK(r->sf == 1);
    CHECK(r->psfi.value == 9);
}
