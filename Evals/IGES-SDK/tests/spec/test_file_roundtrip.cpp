// Full file round-trip: build entities -> write file -> read file -> compare.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "writer/file_writer.hpp"
#include "writer/entity_writer.hpp"
#include "parser/file_reader.hpp"
#include "parser/param_tokenizer.hpp"
#include "entities/line_entity.hpp"
#include "entities/point_entity.hpp"
#include "entities/circular_arc_entity.hpp"
#include "entities/sphere_entity.hpp"
#include <sstream>

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

static GlobalSection make_test_global() {
    GlobalSection g;
    g.product_id_sender = "test";
    g.file_name = "test.igs";
    g.native_system_id = "IGES-SDK";
    g.preprocessor_version = "1.0";
    g.integer_bits = 32;
    g.sp_magnitude = 38;
    g.sp_significance = 6;
    g.dp_magnitude = 308;
    g.dp_significance = 15;
    g.units = Units::Millimeters;
    g.units_name = "MM";
    return g;
}

TEST_CASE("File round-trip -- single line entity", "[file][round-trip]") {
    // Build
    LineEntity le;
    le.start = {1.5, 2.5, 3.5};
    le.terminate = {4.5, 5.5, 6.5};

    DirectoryEntry de;
    de.entity_type = EntityType{110};

    auto file_str = write_iges_file(
        {"Test file with one line entity"},
        make_test_global(),
        {{de, write_line_entity(le)}});

    // Read back
    std::istringstream iss(file_str);
    auto result = read_iges_file(iss);
    REQUIRE(result.has_value());

    auto& f = result.value();
    CHECK(f.global.units == Units::Millimeters);
    REQUIRE(f.entities.size() == 1);
    CHECK(f.entities[0].de.entity_type.value == 110);

    // Parse the PD string
    ParamTokenizer tok(f.entities[0].pd_string,
                       f.global.param_delimiter,
                       f.global.record_delimiter);
    auto r = parse_line_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->start.x, WithinRel(1.5));
    CHECK_THAT(r->start.y, WithinRel(2.5));
    CHECK_THAT(r->start.z, WithinRel(3.5));
    CHECK_THAT(r->terminate.x, WithinRel(4.5));
    CHECK_THAT(r->terminate.y, WithinRel(5.5));
    CHECK_THAT(r->terminate.z, WithinRel(6.5));
}

TEST_CASE("File round-trip -- multiple entities", "[file][round-trip]") {
    LineEntity le;
    le.start = {0, 0, 0};
    le.terminate = {10, 0, 0};

    PointEntity pe;
    pe.coords = {5, 5, 5};
    pe.display_symbol = DEIndex{0};

    CircularArcEntity ca;
    ca.zt = 0.0;
    ca.x1 = 0.0; ca.y1 = 0.0;
    ca.x2 = 1.0; ca.y2 = 0.0;
    ca.x3 = -1.0; ca.y3 = 0.0;

    DirectoryEntry de_line;
    de_line.entity_type = EntityType{110};

    DirectoryEntry de_point;
    de_point.entity_type = EntityType{116};

    DirectoryEntry de_arc;
    de_arc.entity_type = EntityType{100};

    auto file_str = write_iges_file(
        {"Multi-entity test"},
        make_test_global(),
        {{de_line, write_line_entity(le)},
         {de_point, write_point_entity(pe)},
         {de_arc, write_circular_arc_entity(ca)}});

    std::istringstream iss(file_str);
    auto result = read_iges_file(iss);
    REQUIRE(result.has_value());

    auto& f = result.value();
    REQUIRE(f.entities.size() == 3);
    CHECK(f.entities[0].de.entity_type.value == 110);
    CHECK(f.entities[1].de.entity_type.value == 116);
    CHECK(f.entities[2].de.entity_type.value == 100);

    // Verify each entity parses correctly
    {
        ParamTokenizer tok(f.entities[0].pd_string, ',', ';');
        auto r = parse_line_entity(tok);
        REQUIRE(r.has_value());
        CHECK_THAT(r->terminate.x, WithinRel(10.0));
    }
    {
        ParamTokenizer tok(f.entities[1].pd_string, ',', ';');
        auto r = parse_point_entity(tok);
        REQUIRE(r.has_value());
        CHECK_THAT(r->coords.x, WithinRel(5.0));
    }
    {
        ParamTokenizer tok(f.entities[2].pd_string, ',', ';');
        auto r = parse_circular_arc_entity(tok);
        REQUIRE(r.has_value());
        CHECK_THAT(r->x2, WithinRel(1.0));
    }
}

TEST_CASE("File round-trip -- global section preserved", "[file][round-trip]") {
    auto g = make_test_global();
    g.author = "Test Author";
    g.organization = "Test Org";
    g.model_space_scale = 2.5;
    g.min_resolution = 1e-6;
    g.max_coordinate = 1000.0;

    auto file_str = write_iges_file({"Global test"}, g, {});

    std::istringstream iss(file_str);
    auto result = read_iges_file(iss);
    REQUIRE(result.has_value());

    auto& rg = result.value().global;
    CHECK(rg.product_id_sender == "test");
    CHECK(rg.file_name == "test.igs");
    CHECK(rg.native_system_id == "IGES-SDK");
    CHECK(rg.units == Units::Millimeters);
    CHECK(rg.units_name == "MM");
    CHECK(rg.author == "Test Author");
    CHECK(rg.organization == "Test Org");
    CHECK_THAT(rg.model_space_scale, WithinRel(2.5));
    CHECK_THAT(rg.min_resolution, WithinRel(1e-6));
    CHECK_THAT(rg.max_coordinate, WithinRel(1000.0));
}

TEST_CASE("File round-trip -- start section preserved", "[file][round-trip]") {
    auto file_str = write_iges_file(
        {"Line 1 of start section", "Line 2 of start section"},
        make_test_global(), {});

    std::istringstream iss(file_str);
    auto result = read_iges_file(iss);
    REQUIRE(result.has_value());

    REQUIRE(result.value().start_lines.size() == 2);
    CHECK(result.value().start_lines[0] == "Line 1 of start section");
    CHECK(result.value().start_lines[1] == "Line 2 of start section");
}
