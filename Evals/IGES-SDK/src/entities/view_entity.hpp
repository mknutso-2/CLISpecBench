#pragma once
// iges::ViewEntity — Type 410.
//
// §4.134 Form 0: "The View Entity defines a specific window
//   into a model coordinate space."
// §4.135 Form 1: "The Perspective View Entity defines a perspective
//   projection from model space."

#include "../types.hpp"
#include "../parser/param_tokenizer.hpp"
#include "entity.hpp"
#include <expected>
#include <vector>

namespace iges {

struct ViewEntity {
    int form = 0;
    int view_number = 0;
    Real scale = 1.0;
    // Form 0: up to 6 clip plane DE pointers
    std::vector<DEIndex> clip_planes;
    // Form 1 (Perspective View) fields:
    Vec3 view_plane_normal;             // 3-5: VPNX, VPNY, VPNZ
    Vec3 view_reference_point;          // 6-8: VRPX, VRPY, VRPZ
    Vec3 center_of_projection;          // 9-11: CPX, CPY, CPZ
    Vec3 view_up_vector;                // 12-14: VUPX, VUPY, VUPZ
    Real view_plane_distance = 0.0;     // 15: VPD
    Real umin = 0.0;                    // 16: UMIN
    Real umax = 0.0;                    // 17: UMAX
    Real vmin = 0.0;                    // 18: VMIN
    Real vmax = 0.0;                    // 19: VMAX
    int depth_clipping = 0;             // 20: DCI
    Real wmin = 0.0;                    // 21: WMIN
    Real wmax = 0.0;                    // 22: WMAX
};

std::expected<ViewEntity, Diagnostic>
parse_view_entity(ParamTokenizer& tok, int form);

} // namespace iges
