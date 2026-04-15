// iges::ViewEntity — Full implementation.

#include "view_entity.hpp"

namespace iges {

std::expected<ViewEntity, Diagnostic>
parse_view_entity(ParamTokenizer& tok, int form) {
    ViewEntity e;
    e.form = form;

    auto vn = tok.next_integer(); if (!vn) return std::unexpected(vn.error()); e.view_number = *vn;
    auto sc = tok.next_real_or(1.0); if (!sc) return std::unexpected(sc.error()); e.scale = *sc;

    if (form == 1) {
        auto vpnx = tok.next_real(); if (!vpnx) return std::unexpected(vpnx.error()); e.view_plane_normal.x = *vpnx;
        auto vpny = tok.next_real(); if (!vpny) return std::unexpected(vpny.error()); e.view_plane_normal.y = *vpny;
        auto vpnz = tok.next_real(); if (!vpnz) return std::unexpected(vpnz.error()); e.view_plane_normal.z = *vpnz;
        auto vrpx = tok.next_real(); if (!vrpx) return std::unexpected(vrpx.error()); e.view_reference_point.x = *vrpx;
        auto vrpy = tok.next_real(); if (!vrpy) return std::unexpected(vrpy.error()); e.view_reference_point.y = *vrpy;
        auto vrpz = tok.next_real(); if (!vrpz) return std::unexpected(vrpz.error()); e.view_reference_point.z = *vrpz;
        auto cpx = tok.next_real(); if (!cpx) return std::unexpected(cpx.error()); e.center_of_projection.x = *cpx;
        auto cpy = tok.next_real(); if (!cpy) return std::unexpected(cpy.error()); e.center_of_projection.y = *cpy;
        auto cpz = tok.next_real(); if (!cpz) return std::unexpected(cpz.error()); e.center_of_projection.z = *cpz;
        auto vupx = tok.next_real(); if (!vupx) return std::unexpected(vupx.error()); e.view_up_vector.x = *vupx;
        auto vupy = tok.next_real(); if (!vupy) return std::unexpected(vupy.error()); e.view_up_vector.y = *vupy;
        auto vupz = tok.next_real(); if (!vupz) return std::unexpected(vupz.error()); e.view_up_vector.z = *vupz;
        auto vpd = tok.next_real(); if (!vpd) return std::unexpected(vpd.error()); e.view_plane_distance = *vpd;
        auto umin = tok.next_real(); if (!umin) return std::unexpected(umin.error()); e.umin = *umin;
        auto umax = tok.next_real(); if (!umax) return std::unexpected(umax.error()); e.umax = *umax;
        auto vmin = tok.next_real(); if (!vmin) return std::unexpected(vmin.error()); e.vmin = *vmin;
        auto vmax = tok.next_real(); if (!vmax) return std::unexpected(vmax.error()); e.vmax = *vmax;
        auto dci = tok.next_integer(); if (!dci) return std::unexpected(dci.error()); e.depth_clipping = *dci;
        auto wmin = tok.next_real(); if (!wmin) return std::unexpected(wmin.error()); e.wmin = *wmin;
        auto wmax = tok.next_real(); if (!wmax) return std::unexpected(wmax.error()); e.wmax = *wmax;
    } else {
        // Form 0: read remaining clip plane pointers until record end
        while (!tok.at_record_end()) {
            auto p = tok.next_pointer();
            if (!p) break;
            e.clip_planes.push_back(*p);
        }
    }

    return e;
}

} // namespace iges
