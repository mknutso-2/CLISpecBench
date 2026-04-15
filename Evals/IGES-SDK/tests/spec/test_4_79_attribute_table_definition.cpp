// Tests for §4.79 — Attribute Table Definition Entity (Type 322).
// Spec reference: IGES 5.3, §4.79, pages 335-338.

#include <catch2/catch_test_macros.hpp>
#include "entities/attribute_table_definition_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.79 Form 0: definition only — {AT, AVDT, AVC} x NA
// -----------------------------------------------------------------

TEST_CASE("§4.79 — parse Form 0 definition only", "[entity][spec-4.79]") {
    // NAME="ELEC", ALT=2 (electrical), NA=3,
    //   attr1: AT=1, AVDT=2 (real), AVC=1
    //   attr2: AT=3, AVDT=1 (integer), AVC=2
    //   attr3: AT=7, AVDT=3 (string), AVC=1
    ParamTokenizer tok("4HELEC,2,3,"
                       "1,2,1,"
                       "3,1,2,"
                       "7,3,1;", ',', ';');
    auto r = parse_attribute_table_definition_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r->name == "ELEC");
    CHECK(r->alt == 2);
    CHECK(r->na == 3);
    REQUIRE(r->attributes.size() == 3);

    CHECK(r->attributes[0].at == 1);
    CHECK(r->attributes[0].avdt == 2);
    CHECK(r->attributes[0].avc == 1);
    CHECK(r->attributes[0].values.empty());

    CHECK(r->attributes[1].at == 3);
    CHECK(r->attributes[1].avdt == 1);
    CHECK(r->attributes[1].avc == 2);

    CHECK(r->attributes[2].at == 7);
    CHECK(r->attributes[2].avdt == 3);
    CHECK(r->attributes[2].avc == 1);
}

// -----------------------------------------------------------------
// §4.79 Form 1: definition + values
// -----------------------------------------------------------------

TEST_CASE("§4.79 — parse Form 1 with integer values", "[entity][spec-4.79]") {
    // NAME="TEST", ALT=1, NA=1,
    //   AT=5, AVDT=1 (integer), AVC=2, values: 100, 200
    ParamTokenizer tok("4HTEST,1,1,"
                       "5,1,2,100,200;", ',', ';');
    auto r = parse_attribute_table_definition_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->name == "TEST");
    CHECK(r->alt == 1);
    CHECK(r->na == 1);
    REQUIRE(r->attributes.size() == 1);
    CHECK(r->attributes[0].at == 5);
    CHECK(r->attributes[0].avdt == 1);
    CHECK(r->attributes[0].avc == 2);
    REQUIRE(r->attributes[0].values.size() == 2);
    CHECK(std::get<int>(r->attributes[0].values[0]) == 100);
    CHECK(std::get<int>(r->attributes[0].values[1]) == 200);
}

TEST_CASE("§4.79 — parse Form 1 with mixed attribute types", "[entity][spec-4.79]") {
    // NAME="MIX", ALT=1, NA=2,
    //   attr1: AT=1, AVDT=2 (real), AVC=1, value: 3.14
    //   attr2: AT=2, AVDT=3 (string), AVC=1, value: "HELLO"
    ParamTokenizer tok("3HMIX,1,2,"
                       "1,2,1,3.14,"
                       "2,3,1,5HHELLO;", ',', ';');
    auto r = parse_attribute_table_definition_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->na == 2);
    REQUIRE(r->attributes.size() == 2);

    CHECK(r->attributes[0].avdt == 2);
    REQUIRE(r->attributes[0].values.size() == 1);
    CHECK(std::get<Real>(r->attributes[0].values[0]) == 3.14);

    CHECK(r->attributes[1].avdt == 3);
    REQUIRE(r->attributes[1].values.size() == 1);
    CHECK(std::get<std::string>(r->attributes[1].values[0]) == "HELLO");
}

// -----------------------------------------------------------------
// §4.79 Form 2: definition + values + display template pointers
// -----------------------------------------------------------------

TEST_CASE("§4.79 — parse Form 2 with display pointers", "[entity][spec-4.79]") {
    // NAME="FRM2", ALT=1, NA=1,
    //   AT=1, AVDT=1 (integer), AVC=2,
    //   value=42, display_ptr=101, value=99, display_ptr=201
    ParamTokenizer tok("4HFRM2,1,1,"
                       "1,1,2,42,101,99,201;", ',', ';');
    auto r = parse_attribute_table_definition_entity(tok, 2);
    REQUIRE(r.has_value());
    CHECK(r->na == 1);
    REQUIRE(r->attributes.size() == 1);
    auto const& a = r->attributes[0];
    CHECK(a.avc == 2);
    REQUIRE(a.values.size() == 2);
    CHECK(std::get<int>(a.values[0]) == 42);
    CHECK(std::get<int>(a.values[1]) == 99);
    REQUIRE(a.display_ptrs.size() == 2);
    CHECK(a.display_ptrs[0] == DEIndex{101});
    CHECK(a.display_ptrs[1] == DEIndex{201});
}

// -----------------------------------------------------------------
// §4.79 Form 1: pointer-typed attribute values (AVDT=4)
// -----------------------------------------------------------------

TEST_CASE("§4.79 — parse Form 1 with pointer values", "[entity][spec-4.79]") {
    // NAME="PTR", ALT=1, NA=1,
    //   AT=10, AVDT=4 (pointer), AVC=2, values: DE 101, DE 201
    ParamTokenizer tok("3HPTR,1,1,"
                       "10,4,2,101,201;", ',', ';');
    auto r = parse_attribute_table_definition_entity(tok, 1);
    REQUIRE(r.has_value());
    auto const& a = r->attributes[0];
    CHECK(a.avdt == 4);
    REQUIRE(a.values.size() == 2);
    CHECK(std::get<DEIndex>(a.values[0]) == DEIndex{101});
    CHECK(std::get<DEIndex>(a.values[1]) == DEIndex{201});
}

// -----------------------------------------------------------------
// Round-trip: write then parse (Form 0)
// -----------------------------------------------------------------

TEST_CASE("§4.79 — round-trip Form 0", "[entity][spec-4.79]") {
    AttributeTableDefinitionEntity orig;
    orig.name = "ROUNDTRIP";
    orig.alt = 3;
    orig.na = 2;

    AttributeEntry a1;
    a1.at = 5; a1.avdt = 2; a1.avc = 1;
    orig.attributes.push_back(a1);

    AttributeEntry a2;
    a2.at = 10; a2.avdt = 1; a2.avc = 3;
    orig.attributes.push_back(a2);

    auto pd = write_attribute_table_definition_entity(orig, 0);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_attribute_table_definition_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r->name == "ROUNDTRIP");
    CHECK(r->alt == 3);
    CHECK(r->na == 2);
    REQUIRE(r->attributes.size() == 2);
    CHECK(r->attributes[0].at == 5);
    CHECK(r->attributes[0].avdt == 2);
    CHECK(r->attributes[0].avc == 1);
    CHECK(r->attributes[1].at == 10);
    CHECK(r->attributes[1].avdt == 1);
    CHECK(r->attributes[1].avc == 3);
}

// -----------------------------------------------------------------
// Round-trip: write then parse (Form 1 with mixed types)
// -----------------------------------------------------------------

TEST_CASE("§4.79 — round-trip Form 1 with values", "[entity][spec-4.79]") {
    AttributeTableDefinitionEntity orig;
    orig.name = "RT1";
    orig.alt = 1;
    orig.na = 2;

    AttributeEntry a1;
    a1.at = 1; a1.avdt = 1; a1.avc = 2;
    a1.values = {AttributeValue{42}, AttributeValue{99}};
    orig.attributes.push_back(a1);

    AttributeEntry a2;
    a2.at = 2; a2.avdt = 2; a2.avc = 1;
    a2.values = {AttributeValue{Real(2.5)}};
    orig.attributes.push_back(a2);

    auto pd = write_attribute_table_definition_entity(orig, 1);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_attribute_table_definition_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->na == 2);
    CHECK(std::get<int>(r->attributes[0].values[0]) == 42);
    CHECK(std::get<int>(r->attributes[0].values[1]) == 99);
    CHECK(std::get<Real>(r->attributes[1].values[0]) == 2.5);
}

// -----------------------------------------------------------------
// §4.79 Form 1: AVDT=6 (Logical) — parsed as integer per spec
// -----------------------------------------------------------------

TEST_CASE("§4.79 — parse Form 1 with logical values (AVDT=6)", "[entity][spec-4.79]") {
    // §4.79: AVDT=6 is Logical type, stored as integer (0 or 1)
    ParamTokenizer tok("3HLOG,1,1,"
                       "20,6,2,1,0;", ',', ';');
    auto r = parse_attribute_table_definition_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->na == 1);
    auto const& a = r->attributes[0];
    CHECK(a.avdt == 6);
    CHECK(a.avc == 2);
    REQUIRE(a.values.size() == 2);
    CHECK(std::get<int>(a.values[0]) == 1);
    CHECK(std::get<int>(a.values[1]) == 0);
}

// -----------------------------------------------------------------
// Round-trip: write then parse (Form 2 with display pointers)
// -----------------------------------------------------------------

TEST_CASE("§4.79 — round-trip Form 2", "[entity][spec-4.79]") {
    AttributeTableDefinitionEntity orig;
    orig.name = "RT2";
    orig.alt = 1;
    orig.na = 1;

    AttributeEntry a;
    a.at = 1; a.avdt = 1; a.avc = 2;
    a.values = {AttributeValue{10}, AttributeValue{20}};
    a.display_ptrs = {DEIndex{101}, DEIndex{201}};
    orig.attributes.push_back(a);

    auto pd = write_attribute_table_definition_entity(orig, 2);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_attribute_table_definition_entity(tok, 2);
    REQUIRE(r.has_value());
    CHECK(r->name == "RT2");
    CHECK(r->na == 1);
    REQUIRE(r->attributes.size() == 1);
    auto const& ra = r->attributes[0];
    CHECK(ra.avc == 2);
    REQUIRE(ra.values.size() == 2);
    CHECK(std::get<int>(ra.values[0]) == 10);
    CHECK(std::get<int>(ra.values[1]) == 20);
    REQUIRE(ra.display_ptrs.size() == 2);
    CHECK(ra.display_ptrs[0] == DEIndex{101});
    CHECK(ra.display_ptrs[1] == DEIndex{201});
}
