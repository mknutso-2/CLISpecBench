// Round-trip tests batch 2: CSG primitives, B-Rep, structure, annotation.
// parse -> serialize -> re-parse -> compare.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "writer/entity_writer.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// -- CSG primitives --

TEST_CASE("RT-11 -- block entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("2.0,3.0,4.0,1.0,1.0,1.0,1.0,0.0,0.0,0.0,0.0,1.0;", ',', ';');
    auto r1 = parse_block_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_block_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_block_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK_THAT(r2->lx, WithinRel(2.0));
    CHECK_THAT(r2->ly, WithinRel(3.0));
    CHECK_THAT(r2->lz, WithinRel(4.0));
    CHECK_THAT(r2->corner.x, WithinRel(1.0));
}

TEST_CASE("RT-12 -- sphere entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("5.0,1.0,2.0,3.0;", ',', ';');
    auto r1 = parse_sphere_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_sphere_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_sphere_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK_THAT(r2->radius, WithinRel(5.0));
    CHECK_THAT(r2->center.x, WithinRel(1.0));
    CHECK_THAT(r2->center.y, WithinRel(2.0));
    CHECK_THAT(r2->center.z, WithinRel(3.0));
}

TEST_CASE("RT-13 -- torus entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("10.0,2.0,0.0,0.0,0.0,0.0,0.0,1.0;", ',', ';');
    auto r1 = parse_torus_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_torus_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_torus_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK_THAT(r2->r1, WithinRel(10.0));
    CHECK_THAT(r2->r2, WithinRel(2.0));
}

TEST_CASE("RT-14 -- boolean tree entity round-trip", "[writer][round-trip]") {
    // -1, -3, 1 means: operand(DE1), operand(DE3), Union
    ParamTokenizer tok("3,-1,-3,1;", ',', ';');
    auto r1 = parse_boolean_tree_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_boolean_tree_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_boolean_tree_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK(r2->n == 3);
    CHECK(r2->entries[0] == -1);
    CHECK(r2->entries[1] == -3);
    CHECK(r2->entries[2] == 1);
}

TEST_CASE("RT-15 -- solid assembly entity round-trip", "[writer][round-trip]") {
    // Spec §4.48: N, PTR(1)..PTR(N), PTRM(1)..PTRM(N) — two blocks
    ParamTokenizer tok("2,10,20,100,200;", ',', ';');
    auto r1 = parse_solid_assembly_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_solid_assembly_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_solid_assembly_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK(r2->n == 2);
    CHECK(r2->items[0].value == 10);
    CHECK(r2->items[1].value == 20);
    CHECK(r2->transforms[0].value == 100);
    CHECK(r2->transforms[1].value == 200);
}

// -- B-Rep topology --

TEST_CASE("RT-16 -- vertex list entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("2,1.0,2.0,3.0,4.0,5.0,6.0;", ',', ';');
    auto r1 = parse_vertex_list_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_vertex_list_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_vertex_list_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK(r2->n == 2);
    CHECK_THAT(r2->vertices[0].x, WithinRel(1.0));
    CHECK_THAT(r2->vertices[1].z, WithinRel(6.0));
}

TEST_CASE("RT-17 -- face entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("1,2,1,3,5;", ',', ';');
    auto r1 = parse_face_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_face_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_face_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK(r2->surf.value == 1);
    CHECK(r2->n == 2);
    CHECK(r2->outer_loop_flag == true);
    CHECK(r2->loops[0].value == 3);
    CHECK(r2->loops[1].value == 5);
}

TEST_CASE("RT-18 -- shell entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("2,1,1,3,0;", ',', ';');
    auto r1 = parse_shell_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_shell_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_shell_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK(r2->n == 2);
    CHECK(r2->faces[0].face.value == 1);
    CHECK(r2->faces[0].orientation == true);
    CHECK(r2->faces[1].face.value == 3);
    CHECK(r2->faces[1].orientation == false);
}

TEST_CASE("RT-19 -- MSBO entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("1,1,0;", ',', ';');
    auto r1 = parse_msbo_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_msbo_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_msbo_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK(r2->shell.value == 1);
    CHECK(r2->sof == true);
    CHECK(r2->n == 0);
}

// -- Structure + annotation --

TEST_CASE("RT-20 -- subfigure definition entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("0,5HModel,2,1,3;", ',', ';');
    auto r1 = parse_subfigure_definition_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_subfigure_definition_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_subfigure_definition_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK(r2->depth == 0);
    CHECK(r2->name == "Model");
    CHECK(r2->n == 2);
    CHECK(r2->entities[0].value == 1);
}

TEST_CASE("RT-21 -- color definition entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("100.0,0.0,50.0,3HRed;", ',', ';');
    auto r1 = parse_color_definition_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_color_definition_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_color_definition_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK_THAT(r2->red, WithinRel(100.0));
    CHECK_THAT(r2->green, WithinAbs(0.0, 1e-15));
    CHECK_THAT(r2->blue, WithinRel(50.0));
    CHECK(r2->name == "Red");
}

TEST_CASE("RT-22 -- general note entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("1,5,1.0,2.0,1,0.0,0.0,0,0,1.0,2.0,0.0,5Hhello;", ',', ';');
    auto r1 = parse_general_note_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_general_note_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_general_note_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK(r2->ns == 1);
    CHECK(r2->strings[0].text == "hello");
    CHECK_THAT(r2->strings[0].hc, WithinRel(2.0));
}

TEST_CASE("RT-23 -- linear dimension entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("1,3,5,7,9;", ',', ';');
    auto r1 = parse_linear_dimension_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_linear_dimension_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_linear_dimension_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK(r2->denote.value == 1);
    CHECK(r2->dearrw1.value == 3);
    CHECK(r2->dearrw2.value == 5);
    CHECK(r2->dewit1.value == 7);
    CHECK(r2->dewit2.value == 9);
}

TEST_CASE("RT-24 -- leader arrow entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("2,0.5,0.25,0.0,1.0,2.0,3.0,4.0,5.0,6.0;", ',', ';');
    auto r1 = parse_leader_arrow_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_leader_arrow_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_leader_arrow_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK(r2->n == 2);
    CHECK_THAT(r2->ad1, WithinRel(0.5));
    CHECK_THAT(r2->ad2, WithinRel(0.25));
    CHECK(r2->segments.size() == 2);
    CHECK_THAT(r2->segments[0].x, WithinRel(3.0));
}

TEST_CASE("RT-25 -- drawing entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("1,1,0.0,0.0,2,3,5;", ',', ';');
    auto r1 = parse_drawing_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_drawing_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_drawing_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK(r2->n == 1);
    CHECK(r2->views[0].view.value == 1);
    CHECK(r2->m == 2);
    CHECK(r2->annotations[0].value == 3);
}

TEST_CASE("RT-26 -- copious data entity round-trip", "[writer][round-trip]") {
    // IP=2 (3D), N=2 tuples, 6 values total
    ParamTokenizer tok("2,2,1.0,2.0,3.0,4.0,5.0,6.0;", ',', ';');
    auto r1 = parse_copious_data_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_copious_data_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_copious_data_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK(r2->ip == 2);
    CHECK(r2->n == 2);
    CHECK(r2->data.size() == 6);
    CHECK_THAT(r2->data[0], WithinRel(1.0));
    CHECK_THAT(r2->data[5], WithinRel(6.0));
}

TEST_CASE("RT-27 -- associativity instance entity round-trip", "[writer][round-trip]") {
    ParamTokenizer tok("3,1,3,5;", ',', ';');
    auto r1 = parse_associativity_instance_entity(tok);
    REQUIRE(r1.has_value());
    std::string s = write_associativity_instance_entity(*r1);
    ParamTokenizer tok2(s, ',', ';');
    auto r2 = parse_associativity_instance_entity(tok2);
    REQUIRE(r2.has_value());
    CHECK(r2->n == 3);
    CHECK(r2->entries[0].value == 1);
    CHECK(r2->entries[2].value == 5);
}
