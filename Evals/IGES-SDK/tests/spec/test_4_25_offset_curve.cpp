// Tests for §4.25 — Offset Curve Entity (Type 130).
// Written BEFORE implementation (TDD red phase).

#include <catch2/catch_test_macros.hpp>
#include "entities/offset_curve_entity.hpp"
#include "parser/param_tokenizer.hpp"

using namespace iges;

// ─────────────────────────────────────────────────────────────────
// §4.25: "Parameters: DE1, FLAG, DE2, NDIM, PTYPE, D1, TD1,
//   D2, TD2, VX, VY, VZ, TT1, TT2"
// ─────────────────────────────────────────────────────────────────

TEST_CASE("§4.25 — parse offset curve FLAG=1 uniform", "[entity][spec-4.25]") {
    // §4.25: "FLAG=1: The offset distance is uniform; f(s)=D1"
    // Zero-fill unused parameters per spec:
    // "Parameter data not required for a particular case shall be given zero values"
    ParamTokenizer tok("1,1,0,0,0,5.0,0.0,0.0,0.0,0.0,0.0,1.0,0.0,1.0;", ',', ';');
    auto r = parse_offset_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().de1.value == 1);
    CHECK(r.value().flag == 1);
    CHECK(r.value().de2.value == 0);
    CHECK(r.value().d1 == 5.0);
    CHECK(r.value().vz == 1.0);
    CHECK(r.value().tt1 == 0.0);
    CHECK(r.value().tt2 == 1.0);
}

TEST_CASE("§4.25 — parse offset curve FLAG=2 linear", "[entity][spec-4.25]") {
    // §4.25: "FLAG=2: The offset distance varies linearly;
    //   f(s) = D1 + (D2-D1)*(s-TD1)/(TD2-TD1)"
    ParamTokenizer tok("3,2,0,0,1,2.0,0.0,4.0,1.0,0.0,0.0,1.0,0.0,1.0;", ',', ';');
    auto r = parse_offset_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().flag == 2);
    CHECK(r.value().ptype == 1);
    CHECK(r.value().d1 == 2.0);
    CHECK(r.value().td1 == 0.0);
    CHECK(r.value().d2 == 4.0);
    CHECK(r.value().td2 == 1.0);
}

TEST_CASE("§4.25 — parse offset curve FLAG=3 function", "[entity][spec-4.25]") {
    // §4.25: "FLAG=3: The offset distance is defined by a function;
    //   f(s) is the NDIM-th coordinate function of the curve referenced by DE2"
    ParamTokenizer tok("1,3,5,2,2,0.0,0.0,0.0,0.0,0.0,0.0,1.0,0.0,1.0;", ',', ';');
    auto r = parse_offset_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().flag == 3);
    CHECK(r.value().de2.value == 5);
    CHECK(r.value().ndim == 2);
    CHECK(r.value().ptype == 2);
}

TEST_CASE("§4.25 — normal vector components", "[entity][spec-4.25]") {
    // §4.25: "VX, VY, VZ: components of unit vector normal to plane
    //   containing curve to be offset"
    ParamTokenizer tok("1,1,0,0,0,3.0,0.0,0.0,0.0,0.577,0.577,0.577,0.0,2.0;", ',', ';');
    auto r = parse_offset_curve_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r.value().vx == 0.577);
    CHECK(r.value().vy == 0.577);
    CHECK(r.value().vz == 0.577);
}
