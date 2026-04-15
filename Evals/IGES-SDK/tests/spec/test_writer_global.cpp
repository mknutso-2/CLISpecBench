// Tests for Global Section writer — round-trip.
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "writer/global_writer.hpp"
#include "model/global_section.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;

// ─────────────────────────────────────────────────────────────────
// Round-trip: serialize → parse → compare
// ─────────────────────────────────────────────────────────────────

TEST_CASE("Global section round-trip — all 26 fields", "[writer][round-trip]") {
    GlobalSection g;
    g.param_delimiter = ',';
    g.record_delimiter = ';';
    g.product_id_sender = "TestProduct";
    g.file_name = "test.igs";
    g.native_system_id = "IGES-SDK";
    g.preprocessor_version = "v0.1";
    g.integer_bits = 32;
    g.sp_magnitude = 38;
    g.sp_significance = 6;
    g.dp_magnitude = 308;
    g.dp_significance = 15;
    g.product_id_receiver = "Receiver";
    g.model_space_scale = 1.0;
    g.units = Units::Millimeters;
    g.units_name = "MM";
    g.max_line_weight_grads = 4;
    g.max_line_weight_width = 0.01;
    g.file_timestamp = {2026, 4, 11, 12, 0, 0};
    g.min_resolution = 0.0001;
    g.max_coordinate = 1000.0;
    g.author = "John";
    g.organization = "Company";
    g.spec_version = SpecVersion::V5_3;
    g.drafting_std = DraftingStandard::None;
    g.model_timestamp = Timestamp{2026, 4, 11, 12, 0, 0};
    g.app_protocol = "";

    std::string serialized = write_global_section(g);

    // Parse it back
    auto r = parse_global_section(serialized);
    REQUIRE(r.has_value());
    auto& g2 = r.value();

    CHECK(g2.param_delimiter == ',');
    CHECK(g2.record_delimiter == ';');
    CHECK(g2.product_id_sender == "TestProduct");
    CHECK(g2.file_name == "test.igs");
    CHECK(g2.native_system_id == "IGES-SDK");
    CHECK(g2.preprocessor_version == "v0.1");
    CHECK(g2.integer_bits == 32);
    CHECK(g2.sp_magnitude == 38);
    CHECK(g2.sp_significance == 6);
    CHECK(g2.dp_magnitude == 308);
    CHECK(g2.dp_significance == 15);
    CHECK(g2.product_id_receiver == "Receiver");
    CHECK_THAT(g2.model_space_scale, WithinRel(1.0));
    CHECK(g2.units == Units::Millimeters);
    CHECK(g2.units_name == "MM");
    CHECK(g2.max_line_weight_grads == 4);
    CHECK_THAT(g2.max_line_weight_width, WithinRel(0.01));
    CHECK(g2.file_timestamp.year == 2026);
    CHECK_THAT(g2.min_resolution, WithinRel(0.0001));
    CHECK_THAT(g2.max_coordinate, WithinRel(1000.0));
    CHECK(g2.author == "John");
    CHECK(g2.organization == "Company");
    CHECK(g2.spec_version == SpecVersion::V5_3);
    CHECK(g2.drafting_std == DraftingStandard::None);
    REQUIRE(g2.model_timestamp.has_value());
    CHECK(g2.model_timestamp->year == 2026);
}

TEST_CASE("Global section round-trip — minimal with defaults", "[writer][round-trip]") {
    GlobalSection g;
    g.product_id_sender = "Min";
    g.file_name = "min.igs";
    g.native_system_id = "SDK";
    g.preprocessor_version = "v1";
    g.integer_bits = 32;
    g.sp_magnitude = 38;
    g.sp_significance = 6;
    g.dp_magnitude = 308;
    g.dp_significance = 15;
    g.max_line_weight_width = 0.01;
    g.file_timestamp = {2026, 1, 1, 0, 0, 0};
    g.min_resolution = 0.001;

    std::string serialized = write_global_section(g);
    auto r = parse_global_section(serialized);
    REQUIRE(r.has_value());
    CHECK(r.value().product_id_sender == "Min");
    CHECK(r.value().units == Units::Inches);  // default
    CHECK_THAT(r.value().model_space_scale, WithinRel(1.0));  // default
}
