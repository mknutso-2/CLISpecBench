// Tests for §4.29 — Nodal Displacement and Rotation Entity (Type 138).
// Spec reference: IGES 5.3, §4.29, pages 153-154.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/nodal_displacement_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// -----------------------------------------------------------------
// §4.29: "Parameters: NC, GP(1..NC), NN,
//   {NO, NP, X,Y,Z,RX,RY,RZ per NC cases} x NN"
// -----------------------------------------------------------------

TEST_CASE("§4.29 — parse nodal displacement (1 case, 1 node)", "[entity][spec-4.29]") {
    // §4.29 PD: NC=1, GP(1)=1, NN=1, NO(1)=5, NP(1)=3,
    //   X=0.1, Y=0.2, Z=0.3, RX=0.01, RY=0.02, RZ=0.03
    ParamTokenizer tok("1,1,1,5,3,0.1,0.2,0.3,0.01,0.02,0.03;", ',', ';');
    auto r = parse_nodal_displacement_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->nc == 1);
    CHECK(r->gp.size() == 1);
    CHECK(r->gp[0].value == 1);
    CHECK(r->nn == 1);
    REQUIRE(r->nodes.size() == 1);
    CHECK(r->nodes[0].node_id == 5);
    CHECK(r->nodes[0].np.value == 3);
    REQUIRE(r->nodes[0].cases.size() == 1);
    CHECK_THAT(r->nodes[0].cases[0].x,  WithinRel(0.1));
    CHECK_THAT(r->nodes[0].cases[0].y,  WithinRel(0.2));
    CHECK_THAT(r->nodes[0].cases[0].z,  WithinRel(0.3));
    CHECK_THAT(r->nodes[0].cases[0].rx, WithinRel(0.01));
    CHECK_THAT(r->nodes[0].cases[0].ry, WithinRel(0.02));
    CHECK_THAT(r->nodes[0].cases[0].rz, WithinRel(0.03));
}

// -----------------------------------------------------------------
// §4.29: Multiple analysis cases and multiple nodes
// -----------------------------------------------------------------

TEST_CASE("§4.29 — multiple cases and nodes", "[entity][spec-4.29]") {
    // §4.29: NC=2, 2 GP pointers, NN=2, each node has 2 sets of 6 DOF
    NodalDisplacementEntity e;
    e.nc = 2;
    e.gp = {DEIndex{1}, DEIndex{3}};
    e.nn = 2;
    e.nodes = {
        {.node_id = 1, .np = DEIndex{5}, .cases = {
            {.x = 1.0, .y = 2.0, .z = 3.0, .rx = 0.1, .ry = 0.2, .rz = 0.3},
            {.x = 4.0, .y = 5.0, .z = 6.0, .rx = 0.4, .ry = 0.5, .rz = 0.6},
        }},
        {.node_id = 2, .np = DEIndex{7}, .cases = {
            {.x = 7.0, .y = 8.0, .z = 9.0, .rx = 0.7, .ry = 0.8, .rz = 0.9},
            {.x = 10.0, .y = 11.0, .z = 12.0, .rx = 1.0, .ry = 1.1, .rz = 1.2},
        }},
    };

    auto pd = write_nodal_displacement_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_nodal_displacement_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->nc == 2);
    CHECK(r->nn == 2);
    REQUIRE(r->nodes.size() == 2);
    REQUIRE(r->nodes[0].cases.size() == 2);
    CHECK_THAT(r->nodes[0].cases[1].x, WithinRel(4.0));
    CHECK_THAT(r->nodes[1].cases[0].z, WithinRel(9.0));
    CHECK_THAT(r->nodes[1].cases[1].rz, WithinRel(1.2));
}

// -----------------------------------------------------------------
// §4.29: "Rotations expressed in radians"
// -----------------------------------------------------------------

TEST_CASE("§4.29 — zero displacements preserved", "[entity][spec-4.29]") {
    NodalDisplacementEntity e;
    e.nc = 1; e.gp = {DEIndex{1}};
    e.nn = 1;
    e.nodes = {{.node_id = 1, .np = DEIndex{3}, .cases = {
        {.x = 0.0, .y = 0.0, .z = 0.0, .rx = 0.0, .ry = 0.0, .rz = 0.0}
    }}};

    auto pd = write_nodal_displacement_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_nodal_displacement_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->nodes[0].cases[0].x,  WithinAbs(0.0, 1e-15));
    CHECK_THAT(r->nodes[0].cases[0].rz, WithinAbs(0.0, 1e-15));
}

// -----------------------------------------------------------------
// Round-trip: write then parse
// -----------------------------------------------------------------

TEST_CASE("§4.29 — round-trip nodal displacement entity", "[entity][spec-4.29]") {
    NodalDisplacementEntity orig;
    orig.nc = 1;
    orig.gp = {DEIndex{5}};
    orig.nn = 2;
    orig.nodes = {
        {.node_id = 10, .np = DEIndex{11}, .cases = {
            {.x = 0.5, .y = -0.3, .z = 1.2, .rx = 0.001, .ry = -0.002, .rz = 0.003}
        }},
        {.node_id = 20, .np = DEIndex{13}, .cases = {
            {.x = -1.0, .y = 2.5, .z = 0.0, .rx = 0.0, .ry = 0.01, .rz = -0.01}
        }},
    };

    auto pd = write_nodal_displacement_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_nodal_displacement_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->nc == orig.nc);
    CHECK(r->gp[0].value == 5);
    CHECK(r->nn == orig.nn);
    REQUIRE(r->nodes.size() == 2);
    CHECK(r->nodes[0].node_id == 10);
    CHECK_THAT(r->nodes[0].cases[0].x, WithinRel(0.5));
    CHECK_THAT(r->nodes[0].cases[0].ry, WithinRel(-0.002));
    CHECK(r->nodes[1].node_id == 20);
    CHECK_THAT(r->nodes[1].cases[0].y, WithinRel(2.5));
    CHECK_THAT(r->nodes[1].cases[0].rz, WithinRel(-0.01));
}
