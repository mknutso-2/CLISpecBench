// Tests for §4.134/§4.135 — View Entity (Type 410, Forms 0-1).
// Spec reference: IGES 5.3, §4.134 page 493, §4.135 page 497.

#include <catch2/catch_test_macros.hpp>
#include "entities/view_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.134 Form 0: VNO, SCALE, [6 clip plane pointers]
// §4.135 Form 1: VNO, SCALE, VPNX..Z, VRPX..Z, CPX..Z,
//   VUPX..Z, VPD, UMIN, UMAX, VMIN, VMAX, DCI, WMIN, WMAX
// -----------------------------------------------------------------

TEST_CASE("§4.134 — parse view Form 0 basic", "[entity][spec-4.134]") {
    ParamTokenizer tok("1,2.0,0,0,0,0;", ',', ';');
    auto r = parse_view_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r->view_number == 1);
    CHECK(r->scale == 2.0);
}

TEST_CASE("§4.134 — parse view Form 0 with clip planes", "[entity][spec-4.134]") {
    ParamTokenizer tok("1,1.0,3,5,7,9,11,13;", ',', ';');
    auto r = parse_view_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r->view_number == 1);
    CHECK(r->scale == 1.0);
    REQUIRE(r->clip_planes.size() == 6);
    CHECK(r->clip_planes[0].value == 3);
    CHECK(r->clip_planes[5].value == 13);
}

TEST_CASE("§4.135 — parse perspective view Form 1", "[entity][spec-4.135]") {
    // 22 fields: VNO, SCALE, 3xVPN, 3xVRP, 3xCP, 3xVUP, VPD, UMIN, UMAX, VMIN, VMAX, DCI, WMIN, WMAX
    ParamTokenizer tok(
        "1,1.0,"
        "0.0,0.0,1.0,"   // view plane normal
        "0.0,0.0,0.0,"   // view reference point
        "0.0,0.0,100.0," // center of projection
        "0.0,1.0,0.0,"   // view up vector
        "50.0,"           // view plane distance
        "-10.0,10.0,-10.0,10.0," // UMIN, UMAX, VMIN, VMAX
        "3,"              // DCI = back+front
        "-100.0,100.0;",  // WMIN, WMAX
        ',', ';');
    auto r = parse_view_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->view_number == 1);
    CHECK(r->scale == 1.0);
    CHECK(r->view_plane_normal.z == 1.0);
    CHECK(r->center_of_projection.z == 100.0);
    CHECK(r->view_up_vector.y == 1.0);
    CHECK(r->view_plane_distance == 50.0);
    CHECK(r->umin == -10.0);
    CHECK(r->umax == 10.0);
    CHECK(r->vmin == -10.0);
    CHECK(r->vmax == 10.0);
    CHECK(r->depth_clipping == 3);
    CHECK(r->wmin == -100.0);
    CHECK(r->wmax == 100.0);
}

TEST_CASE("§4.134 — round-trip view Form 0 with clip planes", "[entity][spec-4.134]") {
    ViewEntity orig;
    orig.view_number = 1;
    orig.scale = 1.0;
    orig.clip_planes = {DEIndex{3}, DEIndex{5}, DEIndex{7}, DEIndex{9}, DEIndex{11}, DEIndex{13}};

    auto pd = write_view_entity(orig, 0);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_view_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r->view_number == 1);
    CHECK(r->scale == 1.0);
    REQUIRE(r->clip_planes.size() == 6);
    CHECK(r->clip_planes[0].value == 3);
    CHECK(r->clip_planes[5].value == 13);
}

TEST_CASE("§4.135 — round-trip perspective view Form 1", "[entity][spec-4.135]") {
    ViewEntity orig;
    orig.form = 1;
    orig.view_number = 2;
    orig.scale = 0.5;
    orig.view_plane_normal = {0.0, 0.0, 1.0};
    orig.view_reference_point = {1.0, 2.0, 3.0};
    orig.center_of_projection = {0.0, 0.0, 100.0};
    orig.view_up_vector = {0.0, 1.0, 0.0};
    orig.view_plane_distance = 50.0;
    orig.umin = -10.0;
    orig.umax = 10.0;
    orig.vmin = -5.0;
    orig.vmax = 5.0;
    orig.depth_clipping = 1;
    orig.wmin = -200.0;
    orig.wmax = 200.0;

    auto pd = write_view_entity(orig, 1);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_view_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->view_number == 2);
    CHECK(r->scale == 0.5);
    CHECK(r->view_plane_normal.z == 1.0);
    CHECK(r->center_of_projection.z == 100.0);
    CHECK(r->view_up_vector.y == 1.0);
    CHECK(r->view_plane_distance == 50.0);
    CHECK(r->umin == -10.0);
    CHECK(r->umax == 10.0);
    CHECK(r->vmin == -5.0);
    CHECK(r->vmax == 5.0);
    CHECK(r->depth_clipping == 1);
    CHECK(r->wmin == -200.0);
    CHECK(r->wmax == 200.0);
}
