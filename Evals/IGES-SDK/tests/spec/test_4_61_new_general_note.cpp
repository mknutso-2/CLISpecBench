// Tests for §4.61 — New General Note Entity (Type 213).
// Spec reference: IGES 5.3, §4.61, pages 246-256.

#include <catch2/catch_test_macros.hpp>
#include "entities/new_general_note_entity.hpp"
#include "parser/param_tokenizer.hpp"
#include "writer/entity_writer.hpp"

using namespace iges;

// -----------------------------------------------------------------
// §4.61 Basic parse: single string with all 12 header + 20 per-string fields
// -----------------------------------------------------------------

TEST_CASE("§4.61 — parse single text string", "[entity][spec-4.61]") {
    // Header: TXTCW=10.0, TXTCH=5.0, JUSTCD=0, TXTCX=1.0, TXTCY=2.0,
    //         TXTCZ=0.0, TXTAG=0.0, BASELX=1.0, BASELY=2.0, BASELZ=0.0,
    //         NILS=1.5, NS=1
    // String 1: FIXVAR=0, CHRWID=0.7, CHRHGT=1.0, CSPACE=0.1, LSPACE=0.0,
    //           FONT=1, CHRANG=0.0, CCTEXT="TT", NC=5, WT=4.0, HT=1.2,
    //           CHRSET=1, SL=1.5708, A=0.0, M=0, VH=0,
    //           XS=1.0, YS=2.0, ZS=0.0, TEXT="HELLO"
    ParamTokenizer tok("10.0,5.0,0,1.0,2.0,0.0,0.0,1.0,2.0,0.0,1.5,1,"
                       "0,0.7,1.0,0.1,0.0,1,0.0,2HTT,5,4.0,1.2,1,1.5708,0.0,0,0,"
                       "1.0,2.0,0.0,5HHELLO;", ',', ';');
    auto r = parse_new_general_note_entity(tok);
    REQUIRE(r.has_value());

    // Header fields
    CHECK(r->txtcw == 10.0);
    CHECK(r->txtch == 5.0);
    CHECK(r->justcd == 0);
    CHECK(r->txtcx == 1.0);
    CHECK(r->txtcy == 2.0);
    CHECK(r->txtcz == 0.0);
    CHECK(r->txtag == 0.0);
    CHECK(r->baselx == 1.0);
    CHECK(r->basely == 2.0);
    CHECK(r->baselz == 0.0);
    CHECK(r->nils == 1.5);
    CHECK(r->ns == 1);

    // String fields
    REQUIRE(r->strings.size() == 1);
    auto const& s = r->strings[0];
    CHECK(s.fixvar == 0);
    CHECK(s.chrwid == 0.7);
    CHECK(s.chrhgt == 1.0);
    CHECK(s.cspace == 0.1);
    CHECK(s.lspace == 0.0);
    CHECK(s.font == 1);
    CHECK(s.chrang == 0.0);
    CHECK(s.cctext == "TT");
    CHECK(s.nc == 5);
    CHECK(s.wt == 4.0);
    CHECK(s.ht == 1.2);
    CHECK(s.chrset == 1);
    CHECK(s.sl == 1.5708);
    CHECK(s.a == 0.0);
    CHECK(s.m == 0);
    CHECK(s.vh == 0);
    CHECK(s.xs == 1.0);
    CHECK(s.ys == 2.0);
    CHECK(s.zs == 0.0);
    CHECK(s.text == "HELLO");
}

// -----------------------------------------------------------------
// §4.61 Multiple strings
// -----------------------------------------------------------------

TEST_CASE("§4.61 — parse multiple text strings", "[entity][spec-4.61]") {
    // Header: TXTCW=20.0, TXTCH=10.0, JUSTCD=2 (center), TXTCX=0.0,
    //         TXTCY=0.0, TXTCZ=0.0, TXTAG=0.0, BASELX=0.0, BASELY=5.0,
    //         BASELZ=0.0, NILS=2.0, NS=2
    // String 1: FIXVAR=1, CHRWID=0.5, CHRHGT=1.0, CSPACE=0.2, LSPACE=0.0,
    //           FONT=2, CHRANG=0.0, CCTEXT="TU", NC=3, WT=2.0, HT=1.0,
    //           CHRSET=1, SL=1.5708, A=0.0, M=0, VH=0,
    //           XS=0.0, YS=5.0, ZS=0.0, TEXT="ABC"
    // String 2: FIXVAR=0, CHRWID=0.6, CHRHGT=0.8, CSPACE=0.15, LSPACE=2.0,
    //           FONT=1, CHRANG=0.0, CCTEXT="NL", NC=3, WT=2.5, HT=0.9,
    //           CHRSET=1, SL=1.5708, A=0.0, M=1, VH=0,
    //           XS=0.0, YS=3.0, ZS=0.0, TEXT="DEF"
    ParamTokenizer tok("20.0,10.0,2,0.0,0.0,0.0,0.0,0.0,5.0,0.0,2.0,2,"
                       "1,0.5,1.0,0.2,0.0,2,0.0,2HTU,3,2.0,1.0,1,1.5708,0.0,0,0,"
                       "0.0,5.0,0.0,3HABC,"
                       "0,0.6,0.8,0.15,2.0,1,0.0,2HNL,3,2.5,0.9,1,1.5708,0.0,1,0,"
                       "0.0,3.0,0.0,3HDEF;", ',', ';');
    auto r = parse_new_general_note_entity(tok);
    REQUIRE(r.has_value());

    CHECK(r->txtcw == 20.0);
    CHECK(r->justcd == 2);
    CHECK(r->nils == 2.0);
    CHECK(r->ns == 2);
    REQUIRE(r->strings.size() == 2);

    CHECK(r->strings[0].fixvar == 1);
    CHECK(r->strings[0].font == 2);
    CHECK(r->strings[0].cctext == "TU");
    CHECK(r->strings[0].text == "ABC");

    CHECK(r->strings[1].fixvar == 0);
    CHECK(r->strings[1].lspace == 2.0);
    CHECK(r->strings[1].cctext == "NL");
    CHECK(r->strings[1].m == 1);
    CHECK(r->strings[1].ys == 3.0);
    CHECK(r->strings[1].text == "DEF");
}

// -----------------------------------------------------------------
// §4.61 Justification codes
// -----------------------------------------------------------------

TEST_CASE("§4.61 — justification codes", "[entity][spec-4.61]") {
    // §4.61: JUSTCD values 0-3 (none, right, center, left)
    auto make_tok = [](int justcd) {
        std::string pd = "10.0,5.0," + std::to_string(justcd) +
            ",0.0,0.0,0.0,0.0,0.0,0.0,0.0,1.0,1,"
            "0,0.5,1.0,0.1,0.0,1,0.0,2HBL,1,2.0,1.0,1,1.5708,0.0,0,0,"
            "0.0,0.0,0.0,1HA;";
        return pd;
    };
    for (int j = 0; j <= 3; ++j) {
        auto pd = make_tok(j);
        ParamTokenizer tok(pd, ',', ';');
        auto r = parse_new_general_note_entity(tok);
        REQUIRE(r.has_value());
        CHECK(r->justcd == j);
    }
}

// -----------------------------------------------------------------
// §4.61 Mirror and VH flags
// -----------------------------------------------------------------

TEST_CASE("§4.61 — mirror and VH flags", "[entity][spec-4.61]") {
    // §4.61: M=2 (mirror axis is text base line), VH=1 (vertical text)
    ParamTokenizer tok("10.0,5.0,0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1.0,1,"
                       "0,0.5,1.0,0.1,0.0,1,0.0,2HCC,1,2.0,1.0,1,1.5708,0.0,2,1,"
                       "0.0,0.0,0.0,1HX;", ',', ';');
    auto r = parse_new_general_note_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->strings[0].m == 2);
    CHECK(r->strings[0].vh == 1);
}

// -----------------------------------------------------------------
// §4.61 Round-trip: write then parse
// -----------------------------------------------------------------

TEST_CASE("§4.61 — round-trip single string", "[entity][spec-4.61]") {
    NewGeneralNoteEntity orig;
    orig.txtcw = 15.0;
    orig.txtch = 8.0;
    orig.justcd = 3;
    orig.txtcx = 2.0;
    orig.txtcy = 3.0;
    orig.txtcz = 1.0;
    orig.txtag = 0.785;
    orig.baselx = 2.0;
    orig.basely = 3.0;
    orig.baselz = 1.0;
    orig.nils = 1.8;
    orig.ns = 1;

    NewNoteString s;
    s.fixvar = 1;
    s.chrwid = 0.6;
    s.chrhgt = 0.9;
    s.cspace = 0.15;
    s.lspace = 0.0;
    s.font = 14;
    s.chrang = 0.5;
    s.cctext = "BD";
    s.nc = 4;
    s.wt = 3.0;
    s.ht = 1.1;
    s.chrset = 1;
    s.sl = 1.5708;
    s.a = 0.0;
    s.m = 0;
    s.vh = 0;
    s.xs = 2.0;
    s.ys = 3.0;
    s.zs = 1.0;
    s.text = "TEST";
    orig.strings.push_back(s);

    auto pd = write_new_general_note_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_new_general_note_entity(tok);
    REQUIRE(r.has_value());

    CHECK(r->txtcw == 15.0);
    CHECK(r->txtch == 8.0);
    CHECK(r->justcd == 3);
    CHECK(r->txtcx == 2.0);
    CHECK(r->txtag == 0.785);
    CHECK(r->nils == 1.8);
    CHECK(r->ns == 1);

    REQUIRE(r->strings.size() == 1);
    auto const& rs = r->strings[0];
    CHECK(rs.fixvar == 1);
    CHECK(rs.chrwid == 0.6);
    CHECK(rs.chrhgt == 0.9);
    CHECK(rs.font == 14);
    CHECK(rs.chrang == 0.5);
    CHECK(rs.cctext == "BD");
    CHECK(rs.nc == 4);
    CHECK(rs.text == "TEST");
}

// -----------------------------------------------------------------
// §4.61 Round-trip: multiple strings
// -----------------------------------------------------------------

TEST_CASE("§4.61 — round-trip multiple strings", "[entity][spec-4.61]") {
    NewGeneralNoteEntity orig;
    orig.txtcw = 20.0;
    orig.txtch = 10.0;
    orig.justcd = 1;
    orig.txtcx = 0.0;
    orig.txtcy = 0.0;
    orig.txtcz = 0.0;
    orig.txtag = 0.0;
    orig.baselx = 0.0;
    orig.basely = 5.0;
    orig.baselz = 0.0;
    orig.nils = 2.0;
    orig.ns = 2;

    NewNoteString s1;
    s1.fixvar = 0; s1.chrwid = 0.7; s1.chrhgt = 1.0; s1.cspace = 0.1;
    s1.lspace = 0.0; s1.font = 1; s1.chrang = 0.0; s1.cctext = "BL";
    s1.nc = 5; s1.wt = 4.0; s1.ht = 1.2; s1.chrset = 1;
    s1.sl = 1.5708; s1.a = 0.0; s1.m = 0; s1.vh = 0;
    s1.xs = 0.0; s1.ys = 5.0; s1.zs = 0.0; s1.text = "FIRST";
    orig.strings.push_back(s1);

    NewNoteString s2;
    s2.fixvar = 1; s2.chrwid = 0.5; s2.chrhgt = 0.8; s2.cspace = 0.2;
    s2.lspace = 2.0; s2.font = 3; s2.chrang = 0.0; s2.cctext = "NL";
    s2.nc = 6; s2.wt = 3.5; s2.ht = 1.0; s2.chrset = 1;
    s2.sl = 1.5708; s2.a = 0.0; s2.m = 0; s2.vh = 0;
    s2.xs = 0.0; s2.ys = 3.0; s2.zs = 0.0; s2.text = "SECOND";
    orig.strings.push_back(s2);

    auto pd = write_new_general_note_entity(orig);
    ParamTokenizer tok(pd, ',', ';');
    auto r = parse_new_general_note_entity(tok);
    REQUIRE(r.has_value());
    CHECK(r->ns == 2);
    REQUIRE(r->strings.size() == 2);
    CHECK(r->strings[0].text == "FIRST");
    CHECK(r->strings[0].nc == 5);
    CHECK(r->strings[1].text == "SECOND");
    CHECK(r->strings[1].font == 3);
    CHECK(r->strings[1].cctext == "NL");
    CHECK(r->strings[1].lspace == 2.0);
}
