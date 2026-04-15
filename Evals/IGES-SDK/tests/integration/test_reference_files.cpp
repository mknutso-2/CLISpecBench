// Integration tests: parse real-world IGES reference files from Burkardt collection.
// These files are from the IGES specification appendices and NIST.
//
// Sources:
//   ex1.iges — IC semicustom cell (IGES v3.0 Appendix A, modified for v4.0)
//   ex2.iges — Mechanical part with annotation (AUTOFACT 1982, IGES v3.0 Appendix A)
//   ex3.iges — View/Drawing demo with transformation matrices

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "parser/file_reader.hpp"
#include "parser/param_tokenizer.hpp"
#include "model/validate.hpp"
#include "entities/line_entity.hpp"
#include "entities/circular_arc_entity.hpp"
#include "entities/point_entity.hpp"
#include "entities/copious_data_entity.hpp"
#include "entities/subfigure_definition_entity.hpp"
#include "entities/subfigure_instance_entity.hpp"
#include "entities/connect_point_entity.hpp"
#include "entities/property_entity.hpp"
#include "entities/rectangular_array_entity.hpp"
#include "entities/general_note_entity.hpp"
#include "entities/leader_arrow_entity.hpp"
#include "entities/linear_dimension_entity.hpp"
#include "entities/view_entity.hpp"
#include "entities/drawing_entity.hpp"
#include "entities/transformation_matrix_entity.hpp"
#include <fstream>
#include <filesystem>

using namespace iges;
using Catch::Matchers::WithinRel;

// Helper: find test data directory
static std::filesystem::path data_dir() {
    // Try relative to build dir and project root
    for (auto const& candidate : {
        std::filesystem::path("../tests/data"),
        std::filesystem::path("../../tests/data"),
        std::filesystem::path("tests/data"),
    }) {
        if (std::filesystem::exists(candidate)) return candidate;
    }
    return "tests/data";  // fallback
}

static std::optional<IgesFile> load_file(std::string const& name) {
    auto path = data_dir() / name;
    std::ifstream ifs(path);
    if (!ifs.is_open()) return std::nullopt;
    auto result = read_iges_file(ifs);
    if (!result.has_value()) return std::nullopt;
    return std::move(result.value());
}

// -----------------------------------------------------------------
// ex1.iges — IC library cell (subfigures, copious data, connect points)
// -----------------------------------------------------------------

TEST_CASE("ex1.iges -- file parses successfully", "[integration][ex1]") {
    auto file = load_file("ex1.iges");
    REQUIRE(file.has_value());

    // Start section should have 2 lines
    CHECK(file->start_lines.size() == 2);

    // Global section
    CHECK(file->global.product_id_sender == "5MICRONLIB");
    CHECK(file->global.file_name == "PADIN");
    CHECK(file->global.units == Units::Microns);  // unit flag 9

    // Should have entities (21 DE pairs = 42 D lines / 2)
    CHECK(file->entities.size() == 21);
}

TEST_CASE("ex1.iges -- entity types match expectations", "[integration][ex1]") {
    auto file = load_file("ex1.iges");
    REQUIRE(file.has_value());

    // Count entity types
    int type_308 = 0, type_106 = 0, type_320 = 0, type_408 = 0;
    int type_132 = 0, type_412 = 0, type_406 = 0;
    for (auto const& e : file->entities) {
        switch (e.de.entity_type.value) {
            case 308: ++type_308; break;  // Subfigure Definition
            case 106: ++type_106; break;  // Copious Data
            case 320: ++type_320; break;  // Network Subfigure Definition
            case 408: ++type_408; break;  // Subfigure Instance
            case 132: ++type_132; break;  // Connect Point
            case 412: ++type_412; break;  // Rectangular Array
            case 406: ++type_406; break;  // Property
        }
    }
    CHECK(type_308 == 2);   // PADBLK, CONTACT subfigures
    CHECK(type_106 >= 10);  // Many copious data entities
    CHECK(type_406 == 1);   // LINWIDTH property
}

TEST_CASE("ex1.iges -- parse copious data entity from file", "[integration][ex1]") {
    auto file = load_file("ex1.iges");
    REQUIRE(file.has_value());

    // Find first Type 106 entity and parse it
    for (auto const& e : file->entities) {
        if (e.de.entity_type.value == 106) {
            ParamTokenizer tok(e.pd_string,
                               file->global.param_delimiter,
                               file->global.record_delimiter);
            auto r = parse_copious_data_entity(tok);
            REQUIRE(r.has_value());
            CHECK(r->ip >= 1);  // interpretation flag
            CHECK(r->n > 0);    // has data points
            CHECK(!r->data.empty());
            break;
        }
    }
}

// -----------------------------------------------------------------
// ex2.iges — Mechanical part with dimensions and annotations
// -----------------------------------------------------------------

TEST_CASE("ex2.iges -- file parses successfully", "[integration][ex2]") {
    auto file = load_file("ex2.iges");
    REQUIRE(file.has_value());

    CHECK(file->global.product_id_sender == "PANEL123");

    // Should have many entities (complex drawing)
    CHECK(file->entities.size() > 20);
}

TEST_CASE("ex2.iges -- contains geometry and annotation entities", "[integration][ex2]") {
    auto file = load_file("ex2.iges");
    REQUIRE(file.has_value());

    bool has_lines = false, has_arcs = false, has_points = false;
    bool has_notes = false, has_leaders = false, has_dimensions = false;

    for (auto const& e : file->entities) {
        switch (e.de.entity_type.value) {
            case 110: has_lines = true; break;
            case 100: has_arcs = true; break;
            case 116: has_points = true; break;
            case 212: has_notes = true; break;
            case 214: has_leaders = true; break;
            case 216: case 218: case 222: has_dimensions = true; break;
        }
    }

    CHECK(has_lines);
    CHECK(has_arcs);
    CHECK(has_points);
    CHECK(has_notes);
    CHECK(has_leaders);
    CHECK(has_dimensions);
}

TEST_CASE("ex2.iges -- parse line entities from file", "[integration][ex2]") {
    auto file = load_file("ex2.iges");
    REQUIRE(file.has_value());

    int lines_parsed = 0;
    for (auto const& e : file->entities) {
        if (e.de.entity_type.value == 110) {
            ParamTokenizer tok(e.pd_string,
                               file->global.param_delimiter,
                               file->global.record_delimiter);
            auto r = parse_line_entity(tok);
            if (r.has_value()) ++lines_parsed;
        }
    }
    CHECK(lines_parsed > 0);
}

TEST_CASE("ex2.iges -- parse circular arc entities from file", "[integration][ex2]") {
    auto file = load_file("ex2.iges");
    REQUIRE(file.has_value());

    int arcs_parsed = 0;
    for (auto const& e : file->entities) {
        if (e.de.entity_type.value == 100) {
            ParamTokenizer tok(e.pd_string,
                               file->global.param_delimiter,
                               file->global.record_delimiter);
            auto r = parse_circular_arc_entity(tok);
            if (r.has_value()) ++arcs_parsed;
        }
    }
    CHECK(arcs_parsed > 0);
}

// -----------------------------------------------------------------
// ex3.iges — View/Drawing with transformation matrices
// -----------------------------------------------------------------

TEST_CASE("ex3.iges -- file parses successfully", "[integration][ex3]") {
    auto file = load_file("ex3.iges");
    REQUIRE(file.has_value());

    CHECK(file->global.product_id_sender == "VIEWDWG2");

    CHECK(file->entities.size() > 10);
}

TEST_CASE("ex3.iges -- contains view and drawing entities", "[integration][ex3]") {
    auto file = load_file("ex3.iges");
    REQUIRE(file.has_value());

    bool has_view = false, has_drawing = false, has_xform = false;
    for (auto const& e : file->entities) {
        switch (e.de.entity_type.value) {
            case 410: has_view = true; break;
            case 404: has_drawing = true; break;
            case 124: has_xform = true; break;
        }
    }

    CHECK(has_view);
    CHECK(has_drawing);
    CHECK(has_xform);
}

TEST_CASE("ex3.iges -- parse transformation matrices from file", "[integration][ex3]") {
    auto file = load_file("ex3.iges");
    REQUIRE(file.has_value());

    int xforms_parsed = 0;
    for (auto const& e : file->entities) {
        if (e.de.entity_type.value == 124) {
            ParamTokenizer tok(e.pd_string,
                               file->global.param_delimiter,
                               file->global.record_delimiter);
            auto r = parse_transformation_matrix_entity(tok);
            if (r.has_value()) ++xforms_parsed;
        }
    }
    CHECK(xforms_parsed > 0);
}
