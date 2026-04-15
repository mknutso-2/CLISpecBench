// Tests for §2.2.4.4 — Directory Entry Section.
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "model/directory_entry.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §2.2.4.4.9: "The Status Number field is divided into four
//   two-digit subfields"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.4.9 — status number: all zeros", "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9: "The Status Number field is divided into four
    //   two-digit subfields"
    auto r = parse_status_number("00000000");
    REQUIRE(r.has_value());
    // §2.2.4.4.9.1: "00 = Visible"
    CHECK(r.value().blank      == BlankStatus::Visible);
    // §2.2.4.4.9.2: "00 = Independent"
    CHECK(r.value().subordinate == SubordinateSwitch::Independent);
    // §2.2.4.4.9.3: "00 = Geometry"
    CHECK(r.value().entity_use  == EntityUseFlag::Geometry);
    // §2.2.4.4.9.4: "00 = All DE attributes apply ... top down"
    CHECK(r.value().hierarchy   == HierarchyFlag::GlobalTopDown);
}

TEST_CASE("§2.2.4.4.9 — status number: blanked, physically dependent",
          "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9: Parsing "01010000"
    auto r = parse_status_number("01010000");
    REQUIRE(r.has_value());
    // §2.2.4.4.9.1: "01 = Blanked"
    CHECK(r.value().blank      == BlankStatus::Blanked);
    // §2.2.4.4.9.2: "01 = Physically Dependent"
    CHECK(r.value().subordinate == SubordinateSwitch::PhysicallyDependent);
    // §2.2.4.4.9.3: "00 = Geometry"
    CHECK(r.value().entity_use  == EntityUseFlag::Geometry);
    // §2.2.4.4.9.4: "00 = All DE attributes apply ... top down"
    CHECK(r.value().hierarchy   == HierarchyFlag::GlobalTopDown);
}

TEST_CASE("§2.2.4.4.9 — status number: all non-zero subfields",
          "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9: Parsing "01030602"
    auto r = parse_status_number("01030602");
    REQUIRE(r.has_value());
    // §2.2.4.4.9.1: "01 = Blanked"
    CHECK(r.value().blank      == BlankStatus::Blanked);
    // §2.2.4.4.9.2: "03 = Both (Physically and Logically Dependent)"
    CHECK(r.value().subordinate == SubordinateSwitch::Both);
    // §2.2.4.4.9.3: "06 = Construction geometry"
    CHECK(r.value().entity_use  == EntityUseFlag::ConstructionGeometry);
    // §2.2.4.4.9.4: "02 = Use Hierarchy property"
    CHECK(r.value().hierarchy   == HierarchyFlag::UseProperty);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.4.9.1: "Blank Status ... 00=Visible, 01=Blanked"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.4.9.1 — blank status 00 = Visible", "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9.1: "00 = Visible"
    auto r = parse_status_number("00000000");
    REQUIRE(r.has_value());
    CHECK(r.value().blank == BlankStatus::Visible);
}

TEST_CASE("§2.2.4.4.9.1 — blank status 01 = Blanked", "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9.1: "01 = Blanked"
    auto r = parse_status_number("01000000");
    REQUIRE(r.has_value());
    CHECK(r.value().blank == BlankStatus::Blanked);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.4.9.2: "Subordinate Entity Switch ...
//   00=Independent, 01=Physically Dependent,
//   02=Logically Dependent, 03=Both"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.4.9.2 — subordinate 00 = Independent", "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9.2: "00 = Independent"
    auto r = parse_status_number("00000000");
    CHECK(r.value().subordinate == SubordinateSwitch::Independent);
}

TEST_CASE("§2.2.4.4.9.2 — subordinate 01 = PhysicallyDependent", "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9.2: "01 = Physically Dependent"
    auto r = parse_status_number("00010000");
    CHECK(r.value().subordinate == SubordinateSwitch::PhysicallyDependent);
}

TEST_CASE("§2.2.4.4.9.2 — subordinate 02 = LogicallyDependent", "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9.2: "02 = Logically Dependent"
    auto r = parse_status_number("00020000");
    CHECK(r.value().subordinate == SubordinateSwitch::LogicallyDependent);
}

TEST_CASE("§2.2.4.4.9.2 — subordinate 03 = Both", "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9.2: "03 = Both (Physically and Logically Dependent)"
    auto r = parse_status_number("00030000");
    CHECK(r.value().subordinate == SubordinateSwitch::Both);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.4.9.3: "Entity Use Flag ...
//   00=Geometry, 01=Annotation, ..., 05=2D Parametric,
//   06=Construction Geometry"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.4.9.3 — entity use 00 = Geometry", "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9.3: "00 = Geometry"
    auto r = parse_status_number("00000000");
    CHECK(r.value().entity_use == EntityUseFlag::Geometry);
}

TEST_CASE("§2.2.4.4.9.3 — entity use 01 = Annotation", "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9.3: "01 = Annotation"
    auto r = parse_status_number("00000100");
    CHECK(r.value().entity_use == EntityUseFlag::Annotation);
}

TEST_CASE("§2.2.4.4.9.3 — entity use 05 = 2D Parametric", "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9.3: "05 = 2D Parametric"
    auto r = parse_status_number("00000500");
    CHECK(r.value().entity_use == EntityUseFlag::Parametric2D);
}

TEST_CASE("§2.2.4.4.9.3 — entity use 06 = Construction Geometry", "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9.3: "06 = Construction geometry"
    auto r = parse_status_number("00000600");
    CHECK(r.value().entity_use == EntityUseFlag::ConstructionGeometry);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.4.9.4: "Hierarchy ...
//   00=Global top down, 01=Global defer, 02=Use hierarchy property"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.4.9.4 — hierarchy 00 = GlobalTopDown", "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9.4: "00 = All DE attributes apply ... (top down)"
    auto r = parse_status_number("00000000");
    CHECK(r.value().hierarchy == HierarchyFlag::GlobalTopDown);
}

TEST_CASE("§2.2.4.4.9.4 — hierarchy 01 = GlobalDefer", "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9.4: "01 = None of the DE attributes of this entity
    //   apply to its subordinate entities (defer)"
    auto r = parse_status_number("00000001");
    CHECK(r.value().hierarchy == HierarchyFlag::GlobalDefer);
}

TEST_CASE("§2.2.4.4.9.4 — hierarchy 02 = UseProperty", "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9.4: "02 = Individual DE attributes are specified by
    //   the Hierarchy property (Type 406, Form 10)"
    auto r = parse_status_number("00000002");
    CHECK(r.value().hierarchy == HierarchyFlag::UseProperty);
}

// ─────────────────────────────────────────────────────────────────
// §2.2.4.4.9: format_status_number round-trip
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§2.2.4.4.9 — format/parse round-trip", "[model][spec-2.2.4.4]") {
    // §2.2.4.4.9: Verify serialization and deserialization are consistent
    StatusNumber sn;
    sn.blank      = BlankStatus::Blanked;
    sn.subordinate = SubordinateSwitch::Both;
    sn.entity_use  = EntityUseFlag::ConstructionGeometry;
    sn.hierarchy   = HierarchyFlag::UseProperty;

    std::string formatted = format_status_number(sn);
    CHECK(formatted == "01030602");

    auto parsed = parse_status_number(formatted);
    REQUIRE(parsed.has_value());
    CHECK(parsed.value() == sn);
}
