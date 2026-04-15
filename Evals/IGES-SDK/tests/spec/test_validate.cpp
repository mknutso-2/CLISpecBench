// Tests for structural validation.

#include <catch2/catch_test_macros.hpp>
#include "model/validate.hpp"
#include "writer/entity_writer.hpp"
#include "writer/file_writer.hpp"
#include "parser/file_reader.hpp"
#include <sstream>

using namespace iges;

static GlobalSection make_valid_global() {
    GlobalSection g;
    g.product_id_sender = "test";
    g.file_name = "test.igs";
    g.native_system_id = "SDK";
    g.preprocessor_version = "1.0";
    g.integer_bits = 32;
    g.sp_magnitude = 38;
    g.sp_significance = 6;
    g.dp_magnitude = 308;
    g.dp_significance = 15;
    return g;
}

static IgesFile make_valid_file_with_line() {
    auto g = make_valid_global();
    LineEntity le;
    le.start = {0, 0, 0};
    le.terminate = {1, 1, 1};
    DirectoryEntry de;
    de.entity_type = EntityType{110};
    de.param_line_count = 1;

    auto file_str = write_iges_file({"test"}, g, {{de, write_line_entity(le)}});
    std::istringstream iss(file_str);
    auto result = read_iges_file(iss);
    return std::move(result.value());
}

TEST_CASE("validate -- valid file produces no diagnostics", "[validate]") {
    auto file = make_valid_file_with_line();
    auto diags = validate(file);
    CHECK(diags.empty());
}

TEST_CASE("validate -- invalid xform_matrix pointer detected", "[validate]") {
    auto file = make_valid_file_with_line();
    // Set xform_matrix to a non-existent DE
    file.entities[0].de.xform_matrix = DEIndex{999};
    auto diags = validate(file);
    bool found = false;
    for (auto const& d : diags) {
        if (d.message.find("xform_matrix") != std::string::npos) found = true;
    }
    CHECK(found);
}

TEST_CASE("validate -- invalid view pointer detected", "[validate]") {
    auto file = make_valid_file_with_line();
    file.entities[0].de.view = DEIndex{999};
    auto diags = validate(file);
    bool found = false;
    for (auto const& d : diags) {
        if (d.message.find("view") != std::string::npos) found = true;
    }
    CHECK(found);
}

TEST_CASE("validate -- negative entity type detected", "[validate]") {
    auto file = make_valid_file_with_line();
    file.entities[0].de.entity_type = EntityType{-1};
    auto diags = validate(file);
    bool found = false;
    for (auto const& d : diags) {
        if (d.message.find("negative entity type") != std::string::npos) found = true;
    }
    CHECK(found);
}

TEST_CASE("validate -- zero param_line_count for non-null entity", "[validate]") {
    auto file = make_valid_file_with_line();
    file.entities[0].de.param_line_count = 0;
    auto diags = validate(file);
    bool found = false;
    for (auto const& d : diags) {
        if (d.message.find("param_line_count") != std::string::npos) found = true;
    }
    CHECK(found);
}

TEST_CASE("validate -- non-positive model_space_scale", "[validate]") {
    auto file = make_valid_file_with_line();
    file.global.model_space_scale = 0.0;
    auto diags = validate(file);
    bool found = false;
    for (auto const& d : diags) {
        if (d.message.find("model_space_scale") != std::string::npos) found = true;
    }
    CHECK(found);
}

TEST_CASE("validate -- empty file with no entities is valid", "[validate]") {
    IgesFile file;
    file.global = make_valid_global();
    auto diags = validate(file);
    CHECK(diags.empty());
}
