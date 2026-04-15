// Tests for §2.2.4.3 — Global Section (all 26 parameters).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "model/global_section.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;

// ─── Helper: build a minimal valid Global Section string ────────
// All 26 fields, comma-separated, semicolon-terminated.
static const char* kMinimalGlobal =
    "1H,,1H;,"                             // 1,2: delimiters (defaults)
    "7Hproduct,"                            // 3: product ID sender
    "8Htest.igs,"                           // 4: file name
    "10HTestSystem,"                        // 5: native system ID
    "4Hv1.0,"                               // 6: preprocessor version
    "32,"                                   // 7: integer bits
    "38,"                                   // 8: SP magnitude
    "6,"                                    // 9: SP significance
    "308,"                                  // 10: DP magnitude
    "15,"                                   // 11: DP significance
    "7Hproduct,"                            // 12: product ID receiver
    "1.0,"                                  // 13: model space scale
    "1,"                                    // 14: units flag (inches)
    "2HIN,"                                 // 15: units name
    "1,"                                    // 16: max line weight grads
    "0.01,"                                 // 17: max line weight width
    "15H20260411.120000,"                   // 18: file timestamp
    "0.0001,"                               // 19: min resolution
    "1000.0,"                               // 20: max coordinate
    "4HJohn,"                               // 21: author
    "7HCompany,"                            // 22: organization
    "11,"                                   // 23: version flag (5.3)
    "0,"                                    // 24: drafting standard
    "15H20260411.120000,"                   // 25: model timestamp
    ";";                                    // 26: app protocol (defaulted)

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3: Full parse of all 26 fields
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3 — parse all 26 global fields", "[model][spec-2.2.4.3]") {
    // §2.2.4.3: "The Global Section shall contain information describing
    //   the preprocessor ... and information needed by the postprocessor"
    auto r = parse_global_section(kMinimalGlobal);
    REQUIRE(r.has_value());
    auto& g = r.value();

    // §2.2.4.3.1: "Parameter Delimiter Character"
    CHECK(g.param_delimiter  == ',');
    // §2.2.4.3.2: "Record Delimiter Character"
    CHECK(g.record_delimiter == ';');
    // §2.2.4.3.3: "Product Identification From Sender"
    CHECK(g.product_id_sender   == "product");
    // §2.2.4.3.4: "File Name"
    CHECK(g.file_name           == "test.igs");
    // §2.2.4.3.5: "Native System ID"
    CHECK(g.native_system_id    == "TestSystem");
    // §2.2.4.3.6: "Preprocessor Version"
    CHECK(g.preprocessor_version == "v1.0");
    // §2.2.4.3.7: "Number of binary bits for integer representation"
    CHECK(g.integer_bits      == 32);
    // §2.2.4.3.8: "Maximum power of ten ... single precision"
    CHECK(g.sp_magnitude      == 38);
    // §2.2.4.3.9: "Number of significant digits ... single precision"
    CHECK(g.sp_significance   == 6);
    // §2.2.4.3.10: "Maximum power of ten ... double precision"
    CHECK(g.dp_magnitude      == 308);
    // §2.2.4.3.11: "Number of significant digits ... double precision"
    CHECK(g.dp_significance   == 15);
    // §2.2.4.3.12: "Product Identification for the Receiver"
    CHECK(g.product_id_receiver == "product");
    // §2.2.4.3.13: "Model Space Scale"
    CHECK_THAT(g.model_space_scale, WithinRel(1.0));
    // §2.2.4.3.14: "Units Flag"
    CHECK(g.units == Units::Inches);
    // §2.2.4.3.15: "Units Name"
    CHECK(g.units_name == "IN");
    // §2.2.4.3.16: "Maximum Number of Line Weight Gradations"
    CHECK(g.max_line_weight_grads == 1);
    // §2.2.4.3.17: "Width of Maximum Line Weight in Units"
    CHECK_THAT(g.max_line_weight_width, WithinRel(0.01));
    // §2.2.4.3.18: "Date and Time of Exchange File Generation"
    CHECK(g.file_timestamp.year  == 2026);
    CHECK(g.file_timestamp.month == 4);
    CHECK(g.file_timestamp.day   == 11);
    // §2.2.4.3.19: "Minimum User-Intended Resolution"
    CHECK_THAT(g.min_resolution, WithinRel(0.0001));
    // §2.2.4.3.20: "Approximate Maximum Coordinate Value"
    CHECK_THAT(g.max_coordinate, WithinRel(1000.0));
    // §2.2.4.3.21: "Name of Author"
    CHECK(g.author       == "John");
    // §2.2.4.3.22: "Author's Organization"
    CHECK(g.organization == "Company");
    // §2.2.4.3.23: "Version Flag"
    CHECK(g.spec_version  == SpecVersion::V5_3);
    // §2.2.4.3.24: "Drafting Standard Code"
    CHECK(g.drafting_std  == DraftingStandard::None);
    // §2.2.4.3.25: "Date and Time Model was Created or Modified"
    CHECK(g.model_timestamp.has_value());
    CHECK(g.model_timestamp.value().year == 2026);
    // §2.2.4.3.26: "Application protocol/subset identifier"
    CHECK(g.app_protocol.empty());
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.1: "Parameter Delimiter Character ... Default is comma"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.1 — default param delimiter is comma", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.1: "Default is comma"
    auto r = parse_global_section(kMinimalGlobal);
    REQUIRE(r.has_value());
    CHECK(r.value().param_delimiter == ',');
}

TEST_CASE("§2.2.4.3.1 — custom param delimiter", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.1: "Parameter Delimiter Character" (custom via 1H Hollerith)
    std::string data =
        "1H|,1H;|"
        "7Hproduct|8Htest.igs|10HTestSystem|4Hv1.0|"
        "32|38|6|308|15|7Hproduct|1.0|1|2HIN|1|0.01|"
        "15H20260411.120000|0.0001|1000.0|4HJohn|7HCompany|"
        "11|0|15H20260411.120000|;";
    auto r = parse_global_section(data);
    REQUIRE(r.has_value());
    CHECK(r.value().param_delimiter == '|');
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.2: "Record Delimiter Character ... Default is semicolon"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.2 — default record delimiter is semicolon", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.2: "Default is semicolon"
    auto r = parse_global_section(kMinimalGlobal);
    REQUIRE(r.has_value());
    CHECK(r.value().record_delimiter == ';');
}

TEST_CASE("§2.2.4.3.2 — custom record delimiter", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.2: "Record Delimiter Character" (custom via 1H Hollerith)
    std::string data =
        "1H,,1H#,"
        "7Hproduct,8Htest.igs,10HTestSystem,4Hv1.0,"
        "32,38,6,308,15,7Hproduct,1.0,1,2HIN,1,0.01,"
        "15H20260411.120000,0.0001,1000.0,4HJohn,7HCompany,"
        "11,0,15H20260411.120000,#";
    auto r = parse_global_section(data);
    REQUIRE(r.has_value());
    CHECK(r.value().record_delimiter == '#');
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.3: "Product Identification From Sender" (required)
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.3 — product ID sender parsed", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.3: "Product Identification From Sender"
    auto r = parse_global_section(kMinimalGlobal);
    REQUIRE(r.has_value());
    CHECK(r.value().product_id_sender == "product");
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.7-11: Numeric precision fields
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.7 — integer bits parsed", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.7: "Number of binary bits for integer representation"
    auto r = parse_global_section(kMinimalGlobal);
    REQUIRE(r.has_value());
    CHECK(r.value().integer_bits == 32);
}

TEST_CASE("§2.2.4.3.11 — IEEE 64-bit example: DP significance = 15", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.11: "Number of significant digits ... double precision"
    auto r = parse_global_section(kMinimalGlobal);
    REQUIRE(r.has_value());
    CHECK(r.value().dp_significance == 15);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.12: "Product Identification for the Receiver ...
//   Default is the value of Parameter 3"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.12 — receiver ID defaults to sender ID", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.12: "Default is the value of Parameter 3"
    std::string data =
        "1H,,1H;,"
        "7Hproduct,8Htest.igs,10HTestSystem,4Hv1.0,"
        "32,38,6,308,15,,"                  // field 12 defaulted
        "1.0,1,2HIN,1,0.01,"
        "15H20260411.120000,0.0001,1000.0,4HJohn,7HCompany,"
        "11,0,15H20260411.120000,;";
    auto r = parse_global_section(data);
    REQUIRE(r.has_value());
    CHECK(r.value().product_id_receiver == "product");
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.13: "Model Space Scale ... Default is 1.0"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.13 — model scale 0.125 means 1:8", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.13: "Model Space Scale ... A value of 0.125 indicates
    //   a model created at one-eighth actual size"
    std::string data =
        "1H,,1H;,"
        "7Hproduct,8Htest.igs,10HTestSystem,4Hv1.0,"
        "32,38,6,308,15,7Hproduct,"
        "0.125,"                             // model scale = 0.125
        "1,2HIN,1,0.01,"
        "15H20260411.120000,0.0001,1000.0,4HJohn,7HCompany,"
        "11,0,15H20260411.120000,;";
    auto r = parse_global_section(data);
    REQUIRE(r.has_value());
    CHECK_THAT(r.value().model_space_scale, WithinRel(0.125));
}

TEST_CASE("§2.2.4.3.13 — model scale defaults to 1.0", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.13: "Default is 1.0"
    std::string data =
        "1H,,1H;,"
        "7Hproduct,8Htest.igs,10HTestSystem,4Hv1.0,"
        "32,38,6,308,15,7Hproduct,,"        // field 13 defaulted
        "1,2HIN,1,0.01,"
        "15H20260411.120000,0.0001,1000.0,4HJohn,7HCompany,"
        "11,0,15H20260411.120000,;";
    auto r = parse_global_section(data);
    REQUIRE(r.has_value());
    CHECK_THAT(r.value().model_space_scale, WithinRel(1.0));
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.14: "Units Flag ... Value 1=Inches, 2=Millimeters, ..."
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.14 — units flag 2 = Millimeters", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.14: "Value ... 2=Millimeters"
    std::string data =
        "1H,,1H;,"
        "7Hproduct,8Htest.igs,10HTestSystem,4Hv1.0,"
        "32,38,6,308,15,7Hproduct,1.0,"
        "2,2HMM,"                            // units = MM
        "1,0.01,"
        "15H20260411.120000,0.0001,1000.0,4HJohn,7HCompany,"
        "11,0,15H20260411.120000,;";
    auto r = parse_global_section(data);
    REQUIRE(r.has_value());
    CHECK(r.value().units == Units::Millimeters);
    CHECK(r.value().units_name == "MM");
}

TEST_CASE("§2.2.4.3.14 — units flag defaults to 1 (Inches)", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.14: "Value 1=Inches" (default)
    auto r = parse_global_section(kMinimalGlobal);
    REQUIRE(r.has_value());
    CHECK(r.value().units == Units::Inches);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.16: "Maximum Number of Line Weight Gradations"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.16 — max line weight gradations > 0", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.16: "Maximum Number of Line Weight Gradations"
    auto r = parse_global_section(kMinimalGlobal);
    REQUIRE(r.has_value());
    CHECK(r.value().max_line_weight_grads >= 1);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.18: "Date and Time of Exchange File Generation"
//   Format: YYYYMMDD.HHNNSS or YYMMDD.HHNNSS (2-digit year
//   prefixed with 19)
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.18 — 15-char (4-digit year) timestamp", "[parser][spec-2.2.4.3]") {
    // §2.2.4.3.18: "15HYYYYMMDD.HHNNSS" format
    auto r = parse_timestamp("20260411.120000");
    REQUIRE(r.has_value());
    CHECK(r.value().year   == 2026);
    CHECK(r.value().month  == 4);
    CHECK(r.value().day    == 11);
    CHECK(r.value().hour   == 12);
    CHECK(r.value().minute == 0);
    CHECK(r.value().second == 0);
}

TEST_CASE("§2.2.4.3.18 — 13-char (2-digit year) timestamp prefixed with 19", "[parser][spec-2.2.4.3]") {
    // §2.2.4.3.18: "13HYYMMDD.HHNNSS" format — "YY is prefixed by 19"
    auto r = parse_timestamp("960411.120000");
    REQUIRE(r.has_value());
    CHECK(r.value().year == 1996);
}

TEST_CASE("§2.2.4.3.18 — 2-digit year 99 means 1999", "[parser][spec-2.2.4.3]") {
    // §2.2.4.3.18: "YY is prefixed by 19"
    auto r = parse_timestamp("990101.000000");
    REQUIRE(r.has_value());
    CHECK(r.value().year == 1999);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.19: "Minimum User-Intended Resolution"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.19 — minimum resolution parsed", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.19: "Minimum User-Intended Resolution"
    auto r = parse_global_section(kMinimalGlobal);
    REQUIRE(r.has_value());
    CHECK_THAT(r.value().min_resolution, WithinRel(0.0001));
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.20: "Approximate Maximum Coordinate Value ... Default
//   value is 0.0"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.20 — max coordinate 0.0 means unspecified", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.20: "Default value is 0.0"
    std::string data =
        "1H,,1H;,"
        "7Hproduct,8Htest.igs,10HTestSystem,4Hv1.0,"
        "32,38,6,308,15,7Hproduct,1.0,1,2HIN,1,0.01,"
        "15H20260411.120000,0.0001,,"       // field 20 defaulted
        "4HJohn,7HCompany,11,0,15H20260411.120000,;";
    auto r = parse_global_section(data);
    REQUIRE(r.has_value());
    CHECK_THAT(r.value().max_coordinate, WithinRel(0.0));
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.23: "Version Flag ... The default value is 3"
//   Values: 1=1.0, 2=ANSI Y14.26M-1981, 3=2.0, ..., 11=5.3
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.23 — version flag 11 = IGES 5.3", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.23: "11 = 5.3"
    auto r = parse_global_section(kMinimalGlobal);
    REQUIRE(r.has_value());
    CHECK(r.value().spec_version == SpecVersion::V5_3);
}

TEST_CASE("§2.2.4.3.23 — version flag defaults to 3 (V2.0)", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.23: "The default value is 3" which maps to V2.0
    std::string data =
        "1H,,1H;,"
        "7Hproduct,8Htest.igs,10HTestSystem,4Hv1.0,"
        "32,38,6,308,15,7Hproduct,1.0,1,2HIN,1,0.01,"
        "15H20260411.120000,0.0001,1000.0,4HJohn,7HCompany,"
        ",,15H20260411.120000,;";            // fields 23,24 defaulted
    auto r = parse_global_section(data);
    REQUIRE(r.has_value());
    CHECK(r.value().spec_version == SpecVersion::V2_0);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.23: Clamping of unrecognized version values
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.23 — unrecognized value < 1 assigned 3", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.23: Unrecognized values below range are clamped to
    //   the default (3 = V2.0)
    std::string data =
        "1H,,1H;,"
        "7Hproduct,8Htest.igs,10HTestSystem,4Hv1.0,"
        "32,38,6,308,15,7Hproduct,1.0,1,2HIN,1,0.01,"
        "15H20260411.120000,0.0001,1000.0,4HJohn,7HCompany,"
        "0,0,15H20260411.120000,;";          // version = 0 (invalid)
    auto r = parse_global_section(data);
    REQUIRE(r.has_value());
    CHECK(r.value().spec_version == SpecVersion::V2_0);  // clamped to 3
}

TEST_CASE("§2.2.4.3.23 — unrecognized value > 11 assigned 11", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.23: Unrecognized values above range are clamped to
    //   the maximum known (11 = V5.3)
    std::string data =
        "1H,,1H;,"
        "7Hproduct,8Htest.igs,10HTestSystem,4Hv1.0,"
        "32,38,6,308,15,7Hproduct,1.0,1,2HIN,1,0.01,"
        "15H20260411.120000,0.0001,1000.0,4HJohn,7HCompany,"
        "99,0,15H20260411.120000,;";         // version = 99 (too high)
    auto r = parse_global_section(data);
    REQUIRE(r.has_value());
    CHECK(r.value().spec_version == SpecVersion::V5_3);  // clamped to 11
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.24: "Drafting Standard Code ... Default value is 0"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.24 — drafting standard 0 = None", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.24: "0 = No Standard"
    auto r = parse_global_section(kMinimalGlobal);
    REQUIRE(r.has_value());
    CHECK(r.value().drafting_std == DraftingStandard::None);
}

TEST_CASE("§2.2.4.3.24 — drafting standard defaults to 0", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.24: "Default value is 0"
    std::string data =
        "1H,,1H;,"
        "7Hproduct,8Htest.igs,10HTestSystem,4Hv1.0,"
        "32,38,6,308,15,7Hproduct,1.0,1,2HIN,1,0.01,"
        "15H20260411.120000,0.0001,1000.0,4HJohn,7HCompany,"
        "11,,15H20260411.120000,;";          // field 24 defaulted
    auto r = parse_global_section(data);
    REQUIRE(r.has_value());
    CHECK(r.value().drafting_std == DraftingStandard::None);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.25: "Date and Time Model was Created or Modified"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.25 — model timestamp defaults to unspecified", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.25: Model timestamp is optional; default is null
    std::string data =
        "1H,,1H;,"
        "7Hproduct,8Htest.igs,10HTestSystem,4Hv1.0,"
        "32,38,6,308,15,7Hproduct,1.0,1,2HIN,1,0.01,"
        "15H20260411.120000,0.0001,1000.0,4HJohn,7HCompany,"
        "11,0,,;";                           // field 25 defaulted
    auto r = parse_global_section(data);
    REQUIRE(r.has_value());
    CHECK(!r.value().model_timestamp.has_value());
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.3.26: "Application protocol/subset identifier ...
//   Default is Null"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.3.26 — app protocol defaults to empty", "[model][spec-2.2.4.3]") {
    // §2.2.4.3.26: "Default is Null"
    auto r = parse_global_section(kMinimalGlobal);
    REQUIRE(r.has_value());
    CHECK(r.value().app_protocol.empty());
}
