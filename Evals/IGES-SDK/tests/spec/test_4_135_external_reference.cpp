// Tests for §4.138 — External Reference Entity (Type 416).
// Spec reference: IGES 5.3, §4.138, pages 503-505.

#include <catch2/catch_test_macros.hpp>
#include "entities/external_reference_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.138 Form 0: EXTFID + EXTNAM (single definition from file)
// -----------------------------------------------------------------

TEST_CASE("§4.138 — Form 0: single definition from file", "[entity][spec-4.138]") {
    ParamTokenizer tok("8Hpart.igs,5HBlock;", ',', ';');
    auto r = parse_external_reference_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r->filename == "part.igs");
    CHECK(r->entity_name == "Block");
}

// -----------------------------------------------------------------
// §4.138 Form 1: EXTFID only (entire file as single definition)
// -----------------------------------------------------------------

TEST_CASE("§4.138 — Form 1: entire file reference", "[entity][spec-4.138]") {
    ParamTokenizer tok("8Hpart.igs;", ',', ';');
    auto r = parse_external_reference_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->filename == "part.igs");
    CHECK(r->entity_name.empty());
}

// -----------------------------------------------------------------
// §4.138 Form 2: EXTFID + EXTNAM (logical reference)
// -----------------------------------------------------------------

TEST_CASE("§4.138 — Form 2: logical reference", "[entity][spec-4.138]") {
    ParamTokenizer tok("10Hassembly.i,6HFlange;", ',', ';');
    auto r = parse_external_reference_entity(tok, 2);
    REQUIRE(r.has_value());
    CHECK(r->filename == "assembly.i");
    CHECK(r->entity_name == "Flange");
}

// -----------------------------------------------------------------
// Round-trip: Form 0
// -----------------------------------------------------------------

TEST_CASE("§4.138 — round-trip Form 0", "[entity][spec-4.138]") {
    ExternalReferenceEntity orig;
    orig.filename = "test.igs";
    orig.entity_name = "Part1";

    auto pd = write_external_reference_entity(orig, 0);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_external_reference_entity(tok, 0);
    REQUIRE(r.has_value());
    CHECK(r->filename == "test.igs");
    CHECK(r->entity_name == "Part1");
}

// -----------------------------------------------------------------
// Round-trip: Form 1
// -----------------------------------------------------------------

TEST_CASE("§4.138 — round-trip Form 1", "[entity][spec-4.138]") {
    ExternalReferenceEntity orig;
    orig.filename = "lib.igs";

    auto pd = write_external_reference_entity(orig, 1);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_external_reference_entity(tok, 1);
    REQUIRE(r.has_value());
    CHECK(r->filename == "lib.igs");
    CHECK(r->entity_name.empty());
}
