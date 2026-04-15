// Tests for §4.6 — Copious Data Entity (Type 106, Forms 1-3).
// Spec reference: IGES 5.3, §4.6, page 76.

#include <catch2/catch_test_macros.hpp>
#include "entities/copious_data_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.6 PD table (page 76):
//   IP=1 (Form 1): IP, N, ZT, X(1), Y(1), ..., X(N), Y(N)
//   IP=2 (Form 2): IP, N, X(1), Y(1), Z(1), ..., X(N), Y(N), Z(N)
//   IP=3 (Form 3): IP, N, X(1)..K(1), ..., X(N)..K(N)
// -----------------------------------------------------------------

TEST_CASE("§4.6 — parse copious data IP=1 (2D with ZT)", "[entity][spec-4.6]") {
    // IP=1: ZT at index 3, then N x,y pairs
    ParamTokenizer tok("1,3,5.0,1.0,2.0,3.0,4.0,5.0,6.0;", ',', ';');
    auto r = parse_copious_data_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ip == 1);
    CHECK(r->n == 3);
    CHECK(r->zt == 5.0);
    REQUIRE(r->data.size() == 6);  // N * 2
    CHECK(r->data[0] == 1.0);
    CHECK(r->data[1] == 2.0);
}

TEST_CASE("§4.6 — parse copious data IP=2 (3D)", "[entity][spec-4.6]") {
    ParamTokenizer tok("2,2,1.0,2.0,3.0,4.0,5.0,6.0;", ',', ';');
    auto r = parse_copious_data_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ip == 2);
    CHECK(r->n == 2);
    REQUIRE(r->data.size() == 6);  // N * 3
}

TEST_CASE("§4.6 — parse copious data IP=3 (3D + vector)", "[entity][spec-4.6]") {
    ParamTokenizer tok("3,1,1.0,2.0,3.0,0.0,0.0,1.0;", ',', ';');
    auto r = parse_copious_data_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ip == 3);
    CHECK(r->n == 1);
    REQUIRE(r->data.size() == 6);  // N * 6
}

TEST_CASE("§4.6 — Form 40 witness line uses IP=2", "[entity][spec-4.6]") {
    ParamTokenizer tok("2,3,0.0,0.0,0.0,0.0,10.0,0.0,5.0,10.0,0.0;", ',', ';');
    auto r = parse_copious_data_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ip == 2);
    CHECK(r->n == 3);
}

TEST_CASE("§4.6 — round-trip copious data IP=1", "[entity][spec-4.6]") {
    CopiousDataEntity orig;
    orig.ip = 1;
    orig.n = 2;
    orig.zt = 10.0;
    orig.data = {1.0, 2.0, 3.0, 4.0};

    auto pd = write_copious_data_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_copious_data_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ip == 1);
    CHECK(r->n == 2);
    CHECK(r->zt == 10.0);
    REQUIRE(r->data.size() == 4);
    CHECK(r->data[0] == 1.0);
    CHECK(r->data[3] == 4.0);
}

TEST_CASE("§4.6 — round-trip copious data IP=2", "[entity][spec-4.6]") {
    CopiousDataEntity orig;
    orig.ip = 2;
    orig.n = 2;
    orig.data = {1.0, 2.0, 3.0, 4.0, 5.0, 6.0};

    auto pd = write_copious_data_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_copious_data_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ip == 2);
    CHECK(r->n == 2);
    REQUIRE(r->data.size() == 6);
}
