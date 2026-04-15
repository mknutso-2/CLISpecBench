// Tests for §4.67 — General Symbol Entity (Type 228).
// Spec reference: IGES 5.3, §4.67, page 275.

#include <catch2/catch_test_macros.hpp>
#include "entities/general_symbol_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.67: "Parameters: DENOTE, N, DEGEOM(1)..DEGEOM(N),
//   L, DEARRW(1)..DEARRW(L)"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.67 — parse general symbol entity", "[entity][spec-4.67]") {
    // §4.67 PD: "Index 1: DENOTE, 2: N, 3..2+N: DEGEOM(i),
    //   3+N: L, 4+N..3+N+L: DEARRW(i)"
    ParamTokenizer tok("1,2,3,5,1,7;", ',', ';');
    auto r = parse_general_symbol_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == 1);
    CHECK(r->n == 2);
    CHECK(r->geometries.size() == 2);
    CHECK(r->geometries[0].value == 3);
    CHECK(r->geometries[1].value == 5);
    CHECK(r->l == 1);
    CHECK(r->leaders.size() == 1);
    CHECK(r->leaders[0].value == 7);
}

// ─────────────────────────────────────────────────────────────────
// §4.67: Symbol with zero geometries and zero leaders
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.67 — symbol with zero geometries and leaders", "[entity][spec-4.67]") {
    // §4.67: Both N and L can be zero
    ParamTokenizer tok("1,0,0;", ',', ';');
    auto r = parse_general_symbol_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == 1);
    CHECK(r->n == 0);
    CHECK(r->geometries.empty());
    CHECK(r->l == 0);
    CHECK(r->leaders.empty());
}

// ─────────────────────────────────────────────────────────────────
// §4.67: Symbol with geometries but no leaders
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.67 — symbol with geometries only", "[entity][spec-4.67]") {
    // §4.67: L=0, N>0
    GeneralSymbolEntity e;
    e.denote = DEIndex{11};
    e.n = 3;
    e.geometries = {DEIndex{13}, DEIndex{15}, DEIndex{17}};
    e.l = 0;

    auto pd = write_general_symbol_entity(e);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_general_symbol_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->n == 3);
    CHECK(r->geometries.size() == 3);
    CHECK(r->l == 0);
    CHECK(r->leaders.empty());
}

// ─────────────────────────────────────────────────────────────────
// Round-trip: write then parse
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.67 — round-trip general symbol entity", "[entity][spec-4.67]") {
    GeneralSymbolEntity orig;
    orig.denote = DEIndex{41};
    orig.n = 2;
    orig.geometries = {DEIndex{43}, DEIndex{45}};
    orig.l = 2;
    orig.leaders = {DEIndex{47}, DEIndex{49}};

    auto pd = write_general_symbol_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_general_symbol_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->denote.value == orig.denote.value);
    CHECK(r->n == orig.n);
    CHECK(r->geometries[0].value == 43);
    CHECK(r->geometries[1].value == 45);
    CHECK(r->l == orig.l);
    CHECK(r->leaders[0].value == 47);
    CHECK(r->leaders[1].value == 49);
}
