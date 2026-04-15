// Tests for §4.58 — Flag Note Entity (Type 208).
// Spec reference: IGES 5.3, §4.58, page 264.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>
#include "entities/flag_note_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;
using Catch::Matchers::WithinRel;
using Catch::Matchers::WithinAbs;

// ─────────────────────────────────────────────────────────────────
// §4.58: "Parameters: XT, YT, ZT, A, DENOTE, N, DEARRW(1)..DEARRW(N)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.58 — parse flag note entity", "[entity][spec-4.58]") {
    // §4.58 PD: "Index 1: XT, 2: YT, 3: ZT, 4: A (rotation angle),
    //   5: DENOTE, 6: N, 7..6+N: DEARRW(i)"
    ParamTokenizer tok("1.0,2.0,3.0,0.5,11,2,13,15;", ',', ';');
    auto r = parse_flag_note_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->xt, WithinRel(1.0));
    CHECK_THAT(r->yt, WithinRel(2.0));
    CHECK_THAT(r->zt, WithinRel(3.0));
    CHECK_THAT(r->angle, WithinRel(0.5));
    CHECK(r->denote.value == 11);
    CHECK(r->n == 2);
    CHECK(r->leaders.size() == 2);
    CHECK(r->leaders[0].value == 13);
    CHECK(r->leaders[1].value == 15);
}

// ─────────────────────────────────────────────────────────────────
// §4.58: Flag note with zero leaders
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.58 — flag note with zero leaders", "[entity][spec-4.58]") {
    // §4.58: N can be zero (no associated arrows)
    ParamTokenizer tok("0.0,0.0,0.0,0.0,5,0;", ',', ';');
    auto r = parse_flag_note_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->n == 0);
    CHECK(r->leaders.empty());
}

// ─────────────────────────────────────────────────────────────────
// §4.58: "A: Rotation angle in radians"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.58 — rotation angle preserved", "[entity][spec-4.58]") {
    // §4.58: rotation angle A is in radians
    FlagNoteEntity e;
    e.xt = 0.0; e.yt = 0.0; e.zt = 0.0;
    e.angle = 3.14159265358979;
    e.denote = DEIndex{1};
    e.n = 0;

    auto pd = write_flag_note_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_flag_note_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->angle, WithinRel(3.14159265358979));
}

// ─────────────────────────────────────────────────────────────────
// Round-trip: write then parse
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.58 — round-trip flag note entity", "[entity][spec-4.58]") {
    FlagNoteEntity orig;
    orig.xt = 10.0; orig.yt = 20.0; orig.zt = 5.0;
    orig.angle = 0.785;
    orig.denote = DEIndex{3};
    orig.n = 2;
    orig.leaders = {DEIndex{7}, DEIndex{9}};

    auto pd = write_flag_note_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_flag_note_entity(tok);
    REQUIRE(r.has_value());
    CHECK_THAT(r->xt, WithinRel(orig.xt));
    CHECK_THAT(r->yt, WithinRel(orig.yt));
    CHECK_THAT(r->zt, WithinRel(orig.zt));
    CHECK_THAT(r->angle, WithinRel(orig.angle));
    CHECK(r->denote.value == orig.denote.value);
    CHECK(r->n == orig.n);
    CHECK(r->leaders.size() == 2);
    CHECK(r->leaders[0].value == 7);
    CHECK(r->leaders[1].value == 9);
}
