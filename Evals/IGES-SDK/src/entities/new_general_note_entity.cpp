// iges::NewGeneralNoteEntity — Full implementation.

#include "new_general_note_entity.hpp"

namespace iges {

std::expected<NewGeneralNoteEntity, Diagnostic>
parse_new_general_note_entity(ParamTokenizer& tok) {
    NewGeneralNoteEntity e;

    auto txtcw = tok.next_real(); if (!txtcw) return std::unexpected(txtcw.error()); e.txtcw = *txtcw;
    auto txtch = tok.next_real(); if (!txtch) return std::unexpected(txtch.error()); e.txtch = *txtch;
    auto justcd = tok.next_integer(); if (!justcd) return std::unexpected(justcd.error()); e.justcd = *justcd;
    auto txtcx = tok.next_real(); if (!txtcx) return std::unexpected(txtcx.error()); e.txtcx = *txtcx;
    auto txtcy = tok.next_real(); if (!txtcy) return std::unexpected(txtcy.error()); e.txtcy = *txtcy;
    auto txtcz = tok.next_real(); if (!txtcz) return std::unexpected(txtcz.error()); e.txtcz = *txtcz;
    auto txtag = tok.next_real(); if (!txtag) return std::unexpected(txtag.error()); e.txtag = *txtag;
    auto baselx = tok.next_real(); if (!baselx) return std::unexpected(baselx.error()); e.baselx = *baselx;
    auto basely = tok.next_real(); if (!basely) return std::unexpected(basely.error()); e.basely = *basely;
    auto baselz = tok.next_real(); if (!baselz) return std::unexpected(baselz.error()); e.baselz = *baselz;
    auto nils = tok.next_real(); if (!nils) return std::unexpected(nils.error()); e.nils = *nils;
    auto ns = tok.next_integer(); if (!ns) return std::unexpected(ns.error()); e.ns = *ns;

    e.strings.reserve(e.ns);
    for (int i = 0; i < e.ns; ++i) {
        NewNoteString s;
        auto fixvar = tok.next_integer(); if (!fixvar) return std::unexpected(fixvar.error()); s.fixvar = *fixvar;
        auto chrwid = tok.next_real(); if (!chrwid) return std::unexpected(chrwid.error()); s.chrwid = *chrwid;
        auto chrhgt = tok.next_real(); if (!chrhgt) return std::unexpected(chrhgt.error()); s.chrhgt = *chrhgt;
        auto cspace = tok.next_real(); if (!cspace) return std::unexpected(cspace.error()); s.cspace = *cspace;
        auto lspace = tok.next_real(); if (!lspace) return std::unexpected(lspace.error()); s.lspace = *lspace;
        auto font = tok.next_integer(); if (!font) return std::unexpected(font.error()); s.font = *font;
        auto chrang = tok.next_real(); if (!chrang) return std::unexpected(chrang.error()); s.chrang = *chrang;
        auto cctext = tok.next_string(); if (!cctext) return std::unexpected(cctext.error()); s.cctext = *cctext;
        auto nc = tok.next_integer(); if (!nc) return std::unexpected(nc.error()); s.nc = *nc;
        auto wt = tok.next_real(); if (!wt) return std::unexpected(wt.error()); s.wt = *wt;
        auto ht = tok.next_real(); if (!ht) return std::unexpected(ht.error()); s.ht = *ht;
        auto chrset = tok.next_integer(); if (!chrset) return std::unexpected(chrset.error()); s.chrset = *chrset;
        auto sl = tok.next_real(); if (!sl) return std::unexpected(sl.error()); s.sl = *sl;
        auto a = tok.next_real(); if (!a) return std::unexpected(a.error()); s.a = *a;
        auto m = tok.next_integer(); if (!m) return std::unexpected(m.error()); s.m = *m;
        auto vh = tok.next_integer(); if (!vh) return std::unexpected(vh.error()); s.vh = *vh;
        auto xs = tok.next_real(); if (!xs) return std::unexpected(xs.error()); s.xs = *xs;
        auto ys = tok.next_real(); if (!ys) return std::unexpected(ys.error()); s.ys = *ys;
        auto zs = tok.next_real(); if (!zs) return std::unexpected(zs.error()); s.zs = *zs;
        auto text = tok.next_string(); if (!text) return std::unexpected(text.error()); s.text = *text;
        e.strings.push_back(std::move(s));
    }

    return e;
}

} // namespace iges
