// Tests for §4.35 — Nodal Results Entity (Type 146).
// Spec reference: IGES 5.3, §4.35, pages 168-170.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/nodal_results_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// -----------------------------------------------------------------
// §4.35: "Parameters: GNOTE, SCN, TIME, NV, NN,
//   {NODE, NP, V(1..NV)} x NN"
// -----------------------------------------------------------------

TEST_CASE("§4.35 — parse nodal results (1 node, NV=1 temperature)", "[entity][spec-4.35]") {
    // §4.35 Table 8: TYPE form=1 => Temperature, NV=1
    // PD: GNOTE, SCN, TIME, NV, NN, NODE(1), NP(1), V(1)
    ParamTokenizer tok("1,0,0.0,1,1,42,3,100.5;", ',', ';');
    auto r = parse_nodal_results_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->gnote.value == 1);
    CHECK(r->scn == 0);
    CHECK_THAT(r->time, WithinAbs(0.0, 1e-15));
    CHECK(r->nv == 1);
    CHECK(r->nn == 1);
    REQUIRE(r->nodes.size() == 1);
    CHECK(r->nodes[0].node_id == 42);
    CHECK(r->nodes[0].np.value == 3);
    REQUIRE(r->nodes[0].values.size() == 1);
    CHECK_THAT(r->nodes[0].values[0], WithinRel(100.5));
}

// -----------------------------------------------------------------
// §4.35 Table 8: TYPE form=3 => Displacement, NV=3
// -----------------------------------------------------------------

TEST_CASE("§4.35 — parse nodal results (NV=3 displacement, 2 nodes)", "[entity][spec-4.35]") {
    // §4.35 Table 8: TYPE form=3 => Total Displacement (xx, yy, zz), NV=3
    ParamTokenizer tok("5,1,1.5,3,2,"
                       "1,7,0.1,0.2,0.3,"
                       "2,9,0.4,0.5,0.6;", ',', ';');
    auto r = parse_nodal_results_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->gnote.value == 5);
    CHECK(r->scn == 1);
    CHECK_THAT(r->time, WithinRel(1.5));
    CHECK(r->nv == 3);
    CHECK(r->nn == 2);
    REQUIRE(r->nodes.size() == 2);
    CHECK(r->nodes[0].node_id == 1);
    CHECK(r->nodes[0].np.value == 7);
    CHECK_THAT(r->nodes[0].values[0], WithinRel(0.1));
    CHECK_THAT(r->nodes[0].values[1], WithinRel(0.2));
    CHECK_THAT(r->nodes[0].values[2], WithinRel(0.3));
    CHECK(r->nodes[1].node_id == 2);
    CHECK(r->nodes[1].np.value == 9);
    CHECK_THAT(r->nodes[1].values[0], WithinRel(0.4));
    CHECK_THAT(r->nodes[1].values[1], WithinRel(0.5));
    CHECK_THAT(r->nodes[1].values[2], WithinRel(0.6));
}

// -----------------------------------------------------------------
// §4.35: "SCN: If there is no subcase, the value ... shall be zero."
// -----------------------------------------------------------------

TEST_CASE("§4.35 — zero subcase number", "[entity][spec-4.35]") {
    NodalResultsEntity e;
    e.gnote = DEIndex{1}; e.scn = 0; e.time = 0.0;
    e.nv = 1; e.nn = 1;
    e.nodes = {{.node_id = 1, .np = DEIndex{3}, .values = {25.0}}};

    auto pd = write_nodal_results_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_nodal_results_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->scn == 0);
}

// -----------------------------------------------------------------
// §4.35 Table 8: TYPE form=4 => Displacement+Rotation, NV=6
// -----------------------------------------------------------------

TEST_CASE("§4.35 — NV=6 displacement and rotation", "[entity][spec-4.35]") {
    // §4.35 Table 8: TYPE form=4 => Total Displacement and Rotation, NV=6
    NodalResultsEntity e;
    e.gnote = DEIndex{1}; e.scn = 0; e.time = 2.0;
    e.nv = 6; e.nn = 1;
    e.nodes = {{.node_id = 10, .np = DEIndex{5},
                .values = {1.0, 2.0, 3.0, 0.01, 0.02, 0.03}}};

    auto pd = write_nodal_results_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_nodal_results_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->nv == 6);
    REQUIRE(r->nodes[0].values.size() == 6);
    CHECK_THAT(r->nodes[0].values[3], WithinRel(0.01));
    CHECK_THAT(r->nodes[0].values[4], WithinRel(0.02));
    CHECK_THAT(r->nodes[0].values[5], WithinRel(0.03));
}

// -----------------------------------------------------------------
// Round-trip: write then parse
// -----------------------------------------------------------------

TEST_CASE("§4.35 — round-trip nodal results entity", "[entity][spec-4.35]") {
    NodalResultsEntity orig;
    orig.gnote = DEIndex{3};
    orig.scn = 2;
    orig.time = 10.5;
    orig.nv = 3;
    orig.nn = 3;
    orig.nodes = {
        {.node_id = 1, .np = DEIndex{11}, .values = {1.1, 2.2, 3.3}},
        {.node_id = 2, .np = DEIndex{13}, .values = {4.4, 5.5, 6.6}},
        {.node_id = 3, .np = DEIndex{15}, .values = {7.7, 8.8, 9.9}},
    };

    auto pd = write_nodal_results_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_nodal_results_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->gnote.value == 3);
    CHECK(r->scn == 2);
    CHECK_THAT(r->time, WithinRel(10.5));
    CHECK(r->nv == 3);
    CHECK(r->nn == 3);
    REQUIRE(r->nodes.size() == 3);
    for (int i = 0; i < 3; ++i) {
        CHECK(r->nodes[i].node_id == orig.nodes[i].node_id);
        CHECK(r->nodes[i].np.value == orig.nodes[i].np.value);
        REQUIRE(r->nodes[i].values.size() == 3);
        for (int j = 0; j < 3; ++j) {
            CHECK_THAT(r->nodes[i].values[j], WithinRel(orig.nodes[i].values[j]));
        }
    }
}
