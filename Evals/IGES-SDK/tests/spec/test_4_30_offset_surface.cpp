// Tests for §4.30 — Offset Surface Entity (Type 140).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/offset_surface_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.30: "Parameters: NX, NY, NZ, D, DE"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.30 — parse offset surface basic", "[entity][spec-4.30]") {
    // §4.30: "NX, NY, NZ: coordinates of the offset indicator N(Um,Vm)"
    //        "D: distance by which the surface is normally offset"
    //        "DE: Pointer to the DE of the surface entity to be offset"
    ParamTokenizer tok("0.0,0.0,1.0,2.5,7;", ',', ';');
    auto r = parse_offset_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().nx == 0.0);
    CHECK(r.value().ny == 0.0);
    CHECK(r.value().nz == 1.0);
    CHECK(r.value().d == 2.5);
    CHECK(r.value().de.value == 7);
}

TEST_CASE("§4.30 — negative offset distance", "[entity][spec-4.30]") {
    // §4.30: "offset on the side of the offset indicator if d > 0
    //   and on the opposite side if d < 0"
    ParamTokenizer tok("1.0,0.0,0.0,-1.5,3;", ',', ';');
    auto r = parse_offset_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().d == -1.5);
}

TEST_CASE("§4.30 — offset indicator vector", "[entity][spec-4.30]") {
    // §4.30: "(NX, NY, NZ) = N(Um, Vm) / |N(Um, Vm)| ...
    //   indicates the direction in which the offset distance d
    //   is measured positive"
    ParamTokenizer tok("0.577,0.577,0.577,1.0,11;", ',', ';');
    auto r = parse_offset_surface_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().nx == 0.577);
    CHECK(r.value().ny == 0.577);
    CHECK(r.value().nz == 0.577);
}
